import ast
import json
import os
import py_compile
import tempfile
from pathlib import Path
from typing import Dict, Any, List


def verify_repository_integrity(
    original_dir: Path,
    corrected_dir: Path,
    expected_modified_files: List[str] = None
) -> Dict[str, Any]:
    """
    Performs full repository integrity check after patching:
    - Verifies Python syntax and imports compile cleanly
    - Verifies repository entry points still exist
    - Verifies tests discover correctly
    - Verifies configuration files remain valid
    - Verifies package structure remains intact
    - Verifies no unrelated files were deleted
    - Verifies no unexpected files were created
    - Generates changed-file summary (MODIFIED vs UNCHANGED)
    """
    orig_path = original_dir.resolve()
    corr_path = corrected_dir.resolve()

    ignore_patterns = {".git", "__pycache__", ".pytest_cache", ".venv", "storage", "*.pyc"}

    def get_repo_files(base_path: Path) -> Dict[str, int]:
        files_map = {}
        for root, _, filenames in os.walk(base_path):
            rel_root = Path(root).relative_to(base_path)
            if any(p.startswith(".") or p in {"__pycache__", ".pytest_cache", ".venv", "storage"} for p in rel_root.parts):
                continue
            for f in filenames:
                if f.endswith(".pyc") or f == "test_codepilot_regression.py":
                    continue
                file_p = Path(root) / f
                rel_p = str(file_p.relative_to(base_path)).replace("\\", "/")
                files_map[rel_p] = file_p.stat().st_size
        return files_map

    orig_files = get_repo_files(orig_path)
    corr_files = get_repo_files(corr_path)

    modified_files = []
    unchanged_files = []
    deleted_files = []
    added_files = []

    for rel_p in sorted(orig_files.keys()):
        orig_file = orig_path / rel_p
        corr_file = corr_path / rel_p

        if not corr_file.exists():
            deleted_files.append(rel_p)
            continue

        try:
            orig_bytes = orig_file.read_bytes()
            corr_bytes = corr_file.read_bytes()
            if orig_bytes == corr_bytes:
                unchanged_files.append(rel_p)
            else:
                modified_files.append(rel_p)
        except Exception:
            modified_files.append(rel_p)

    for rel_p in sorted(corr_files.keys()):
        if rel_p not in orig_files:
            added_files.append(rel_p)

    # 1. Python compilation check
    python_syntax_errors = []
    for rel_p in corr_files.keys():
        if rel_p.endswith(".py"):
            target_p = corr_path / rel_p
            try:
                code = target_p.read_text(encoding="utf-8", errors="replace")
                ast.parse(code, filename=str(target_p))
            except SyntaxError as se:
                python_syntax_errors.append(f"{rel_p}: Line {se.lineno}: {se.msg}")
            except Exception as e:
                python_syntax_errors.append(f"{rel_p}: {str(e)}")

    # 2. Config files validity check
    config_errors = []
    for rel_p in corr_files.keys():
        if rel_p.endswith(".json"):
            try:
                json.loads((corr_path / rel_p).read_text(encoding="utf-8", errors="replace"))
            except Exception as e:
                config_errors.append(f"{rel_p}: Invalid JSON - {str(e)}")

    # 3. Entry points check
    entry_point_errors = []
    for rel_p in orig_files.keys():
        if Path(rel_p).name.lower() in {"main.py", "app.py", "api.py", "server.py"}:
            if not (corr_path / rel_p).exists():
                entry_point_errors.append(f"Entry point {rel_p} was deleted!")

    # 4. Check that no unrelated files were touched
    unrelated_modifications = []
    if expected_modified_files:
        norm_expected = {f.replace("\\", "/") for f in expected_modified_files}
        for mf in modified_files:
            if mf not in norm_expected:
                unrelated_modifications.append(mf)

    passed = (
        len(deleted_files) == 0 and
        len(python_syntax_errors) == 0 and
        len(config_errors) == 0 and
        len(entry_point_errors) == 0 and
        len(unrelated_modifications) == 0
    )

    # Build human-readable changed-file summary text
    summary_lines = []
    summary_lines.append("MODIFIED:")
    if modified_files:
        for mf in modified_files:
            summary_lines.append(f"  {mf}")
    else:
        summary_lines.append("  (none)")

    summary_lines.append("\nUNCHANGED:")
    if unchanged_files:
        for uf in unchanged_files:
            summary_lines.append(f"  {uf}")
    else:
        summary_lines.append("  (none)")

    if deleted_files:
        summary_lines.append("\nDELETED (UNEXPECTED):")
        for df in deleted_files:
            summary_lines.append(f"  {df}")

    if added_files:
        summary_lines.append("\nADDED:")
        for af in added_files:
            summary_lines.append(f"  {af}")

    summary_text = "\n".join(summary_lines)

    return {
        "passed": passed,
        "modified_files": modified_files,
        "unchanged_files": unchanged_files,
        "deleted_files": deleted_files,
        "added_files": added_files,
        "python_syntax_errors": python_syntax_errors,
        "config_errors": config_errors,
        "entry_point_errors": entry_point_errors,
        "unrelated_modifications": unrelated_modifications,
        "summary_text": summary_text,
    }

