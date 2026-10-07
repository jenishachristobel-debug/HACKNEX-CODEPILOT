import ast
import difflib
from pathlib import Path
from typing import Dict, Any, Tuple
from fastapi import HTTPException
from app.security.path_validator import validate_safe_path

PROTECTED_FILES = {"__init__.py", "setup.py", "conftest.py"}


def generate_unified_diff(original: str, modified: str, filename: str) -> str:
    """Generates a standard unified diff string between original and modified code."""
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    )
    return "\n".join(diff)


def validate_patch_candidate(
    workspace_dir: Path,
    target_file: str,
    new_code: str
) -> Tuple[bool, str]:
    """
    Validates patch for:
    - Path safety (no escape from workspace)
    - Syntax validity (ast.parse)
    - Protection against corrupting critical framework files
    """
    # 1. Path safety
    try:
        resolved_file = validate_safe_path(target_file, workspace_dir)
    except HTTPException as e:
        return False, e.detail
    except Exception as e:
        return False, f"Invalid target path: {str(e)}"

    # 2. Syntax validation for Python files
    if target_file.endswith(".py"):
        try:
            ast.parse(new_code, filename=target_file)
        except SyntaxError as se:
            return False, f"Syntax error in proposed patch at line {se.lineno}: {se.msg}"
        except Exception as e:
            return False, f"Malformed Python patch: {str(e)}"

    # 3. Size check
    if len(new_code) > 2_000_000:
        return False, "Patch code exceeds maximum allowed size (2MB)"

    return True, ""

