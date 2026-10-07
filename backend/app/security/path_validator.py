import os
from pathlib import Path
from fastapi import HTTPException


def validate_safe_path(target_file: str, base_dir: Path) -> Path:
    """
    Validates that a relative file path does not escape the base directory.
    Rejects absolute paths, backslashes/forward slashes attempting directory traversal.
    """
    if not target_file or not isinstance(target_file, str):
        raise HTTPException(status_code=400, detail="Invalid target file path")

    clean_target = target_file.strip().replace("\\", "/")

    # Reject obvious traversal attempts
    if ".." in clean_target.split("/") or clean_target.startswith("/"):
        raise HTTPException(status_code=400, detail=f"Invalid target file '{target_file}': path traversal not permitted")

    # Reject absolute Windows paths like C:\
    if ":" in clean_target:
        raise HTTPException(status_code=400, detail=f"Invalid target file '{target_file}': absolute drive paths not permitted")

    try:
        resolved_base = base_dir.resolve()
        resolved_target = (resolved_base / clean_target).resolve()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid path resolution: {str(e)}")

    if not str(resolved_target).startswith(str(resolved_base)):
        raise HTTPException(status_code=400, detail=f"Invalid target file: '{target_file}' escapes workspace boundary")

    return resolved_target

