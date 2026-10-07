import ast
from pathlib import Path
from typing import Dict, Any, List


def analyze_change_impact(
    repo_dir: Path,
    target_file: str,
    original_code: str,
    new_code: str
) -> Dict[str, Any]:
    """
    Analyzes blast radius of a patch:
    - Identifies modified functions and classes
    - Discovers other files importing the target file
    - Recommends related test files to run
    """
    repo_path = repo_dir.resolve()
    target_stem = Path(target_file).stem

    # Extract modified functions
    orig_funcs = set()
    new_funcs = set()
    try:
        orig_tree = ast.parse(original_code)
        for node in ast.walk(orig_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                orig_funcs.add(node.name)
    except Exception:
        pass

    try:
        new_tree = ast.parse(new_code)
        for node in ast.walk(new_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                new_funcs.add(node.name)
    except Exception:
        pass

    affected_funcs = list(orig_funcs.intersection(new_funcs))
    if not affected_funcs:
        affected_funcs = list(new_funcs)

    # Search for callers / importers across repo
    dependent_files = []
    recommended_tests = []

    for py_file in repo_path.rglob("*.py"):
        rel_str = str(py_file.relative_to(repo_path)).replace("\\", "/")
        if rel_str == target_file:
            continue

        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
            if target_stem in content or any(fn in content for fn in affected_funcs):
                dependent_files.append(rel_str)
                if "test" in rel_str.lower():
                    recommended_tests.append(rel_str)
        except Exception:
            continue

    risk_level = "LOW"
    if len(dependent_files) > 3 or len(affected_funcs) > 2:
        risk_level = "MEDIUM"
    if len(dependent_files) > 8:
        risk_level = "HIGH"

    return {
        "target_file": target_file,
        "affected_functions": affected_funcs,
        "dependent_files": dependent_files,
        "recommended_tests": recommended_tests,
        "risk_level": risk_level,
        "blast_radius_summary": f"Modifies {len(affected_funcs)} function(s) with {len(dependent_files)} dependent module(s)."
    }

