import io
import os
import shutil
import stat
import zipfile
from pathlib import Path
from typing import List, Tuple
from fastapi import HTTPException
from app.config import settings

SENSITIVE_FILES = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"
}

SENSITIVE_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".secret"}

IGNORED_DIRECTORIES = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}


def is_symlink(zip_info: zipfile.ZipInfo) -> bool:
    mode = zip_info.external_attr >> 16
    return stat.S_ISLNK(mode) != 0


def is_ignored_path(parts: List[str]) -> bool:
    if any(part in IGNORED_DIRECTORIES for part in parts):
        return True
    base_name = parts[-1].lower() if parts else ""
    if base_name in SENSITIVE_FILES or any(base_name.endswith(ext) for ext in SENSITIVE_EXTENSIONS):
        return True
    return False


def validate_and_extract_archive(zip_bytes: bytes, destination_dir: Path) -> List[Tuple[str, int]]:
    """
    Validates ZIP file for safety:
    - Non-empty archive within bounds (25 MB max)
    - Valid ZIP archive structure
    - Non-empty file list
    - No path traversal (e.g. '../', '..\\', Windows drive letters, absolute paths)
    - No symlinks (raises 400 with 'symlink')
    - Max uncompressed size and file count
    - Excludes secrets & .git internals
    Extracts safe files into destination_dir and returns list of (relative_path, size).
    """
    if not zip_bytes or len(zip_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(zip_bytes) > settings.MAX_ARCHIVE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Archive size exceeds maximum allowed limit of {settings.MAX_ARCHIVE_SIZE_BYTES // (1024 * 1024)}MB"
        )

    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except (zipfile.BadZipFile, zipfile.LargeZipFile):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid ZIP archive")

    file_list = zf.infolist()
    if not file_list:
        raise HTTPException(status_code=400, detail="ZIP archive is empty")

    destination_dir = destination_dir.resolve()
    seen_normalized_paths = set()

    WINDOWS_RESERVED_NAMES = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }

    # Pass 1: Symlink, zip bomb, suspicious entries, and path traversal safety checks
    for info in file_list:
        # 1. Symlink check
        if is_symlink(info):
            raise HTTPException(status_code=400, detail=f"Symlink entries are not permitted in archive: {info.filename}")

        # 2. Suspicious character check (null bytes, control chars)
        raw_name = info.filename
        if "\x00" in raw_name or any(ord(c) < 32 and c not in "\t\n\r" for c in raw_name):
            raise HTTPException(status_code=400, detail=f"Suspicious control character detected in archive entry: {info.filename}")

        # 3. Path traversal checks (Unix and Windows variants)
        norm_name = raw_name.replace("\\", "/")
        parts = [p for p in norm_name.split("/") if p]

        # Check for reserved device names on Windows
        for part in parts:
            part_stem = part.split(".")[0].upper()
            if part_stem in WINDOWS_RESERVED_NAMES:
                raise HTTPException(status_code=400, detail=f"Suspicious device name entry detected in archive: {info.filename}")

        # Check for traversal patterns:
        # - ".." in parts
        # - leading slash or backslash
        # - Windows drive letter (e.g. C:)
        # - colon in any segment
        is_traversal = (
            ".." in parts
            or raw_name.startswith("/")
            or raw_name.startswith("\\")
            or norm_name.startswith("/")
            or (len(raw_name) > 1 and raw_name[1] == ":" and raw_name[0].isalpha())
            or any(":" in p for p in parts)
        )
        if is_traversal:
            raise HTTPException(status_code=400, detail=f"Path traversal detected in archive entry: {info.filename}")

        # Path resolution containment check
        try:
            target_path = destination_dir.joinpath(*parts).resolve()
            if not target_path.is_relative_to(destination_dir):
                raise HTTPException(status_code=400, detail=f"Path traversal detected in archive entry: {info.filename}")
        except (ValueError, RuntimeError):
            raise HTTPException(status_code=400, detail=f"Path traversal detected in archive entry: {info.filename}")

        # 4. Zip bomb detection: compression ratio > 100:1 for entries > 1MB
        if info.compress_size > 0 and info.file_size > 1024 * 1024:
            ratio = info.file_size / info.compress_size
            if ratio > 100:
                raise HTTPException(status_code=400, detail="Zip bomb detected: compression ratio exceeds safety limits")

        # 5. Duplicate entry path detection
        normalized_str = "/".join(parts).lower()
        if not info.is_dir() and normalized_str in seen_normalized_paths:
            raise HTTPException(status_code=400, detail=f"Duplicate conflicting entry detected in archive: {info.filename}")
        if not info.is_dir() and parts:
            seen_normalized_paths.add(normalized_str)

    # Pass 2: Filter extractable non-ignored files
    extractable_entries: List[Tuple[zipfile.ZipInfo, List[str]]] = []
    total_uncompressed_size = 0

    for info in file_list:
        norm_name = info.filename.replace("\\", "/")
        parts = [p for p in norm_name.split("/") if p]

        if info.is_dir() or not parts:
            continue

        if is_ignored_path(parts):
            continue

        extractable_entries.append((info, parts))
        total_uncompressed_size += info.file_size

    if not extractable_entries:
        raise HTTPException(status_code=400, detail="ZIP archive contains no extractable files")

    if len(extractable_entries) > settings.MAX_EXTRACTED_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Archive contains {len(extractable_entries)} files, exceeding maximum of {settings.MAX_EXTRACTED_FILES}"
        )

    if total_uncompressed_size > settings.MAX_EXTRACTED_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Archive uncompressed size exceeds limit of {settings.MAX_EXTRACTED_SIZE_BYTES // (1024 * 1024)}MB"
        )

    # Pass 2.5: Detect and unnest single top-level directory wrapper if all files are inside it
    if extractable_entries and all(len(p) > 1 for _, p in extractable_entries):
        common_root = extractable_entries[0][1][0]
        if all(p[0] == common_root for _, p in extractable_entries):
            # All files reside in a single top-level folder (e.g. 'bugfix_auth_api/')
            extractable_entries = [(info, parts[1:]) for info, parts in extractable_entries]

    # Pass 3: Safe extraction
    destination_dir.mkdir(parents=True, exist_ok=True)
    extracted_files: List[Tuple[str, int]] = []

    try:
        for info, parts in extractable_entries:
            target_path = destination_dir.joinpath(*parts).resolve()
            if not target_path.is_relative_to(destination_dir):
                raise HTTPException(status_code=400, detail=f"Path traversal detected in archive entry: {info.filename}")

            target_path.parent.mkdir(parents=True, exist_ok=True)

            with zf.open(info) as src, open(target_path, "wb") as dst:
                dst.write(src.read())

            relative_str = "/".join(parts)
            extracted_files.append((relative_str, info.file_size))
    except Exception:
        if destination_dir.exists():
            shutil.rmtree(destination_dir, ignore_errors=True)
        raise

    return extracted_files
