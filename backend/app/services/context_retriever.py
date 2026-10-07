import re
from pathlib import Path
from typing import Dict, Any, List, Tuple


def retrieve_relevant_context(
    repo_dir: Path,
    bug_title: str,
    bug_description: str,
    error_traceback: str = "",
    symbols: Dict[str, Any] = None,
    max_files: int = 5,
    max_file_size: int = 50_000
) -> List[Dict[str, Any]]:
    """
    Ranks repository files by relevance to the bug report and traceback,
    prioritizing non-test source files for bug repairs while including related tests.
    """
    repo_path = repo_dir.resolve()
    scored_files: List[Tuple[float, str, Path, bool]] = []

    search_text = f"{bug_title} {bug_description} {error_traceback}".lower()
    traceback_matches = set(re.findall(r'[\'"]?([a-zA-Z0-9_\-/\\]+\.py)[\'"]?', search_text))

    for py_file in repo_path.rglob("*.py"):
        rel_str = str(py_file.relative_to(repo_path)).replace("\\", "/")
        parts = rel_str.split("/")
        if any(p.startswith(".") or p in {"__pycache__", ".venv", "storage"} for p in parts):
            continue

        score = 0.0
        filename_lower = py_file.name.lower()
        is_test = "test" in rel_str.lower()

        # Direct traceback mention
        if any(m in rel_str.lower() or m == filename_lower for m in traceback_matches):
            score += 50.0

        # Mentioned in bug title or description (require whole-word match for short stems like 'app')
        if len(py_file.stem) <= 3:
            if re.search(rf"\b{re.escape(py_file.stem.lower())}\b", search_text):
                score += 25.0
        elif py_file.stem.lower() in search_text:
            score += 25.0

        # Symbol match
        if symbols and rel_str in symbols:
            file_symbols = symbols[rel_str]
            for fn in file_symbols.get("functions", []):
                fn_name = fn["name"].lower()
                if fn_name in search_text and len(fn_name) > 3:
                    score += 35.0
                elif any(word in fn_name for word in ["discount", "shipping", "price", "calculate", "tier"] if word in search_text):
                    score += 30.0

            for cl in file_symbols.get("classes", []):
                cl_name = cl["name"].lower()
                if cl_name in search_text:
                    score += 20.0

        # Prefer non-test production code as primary fix targets
        if not is_test:
            score += 10.0

        if score > 0:
            scored_files.append((score, rel_str, py_file, is_test))

    # Sort descending by score
    scored_files.sort(key=lambda x: x[0], reverse=True)

    results = []
    if not scored_files:
        all_py = [p for p in repo_path.rglob("*.py") if not any(x in str(p) for x in ["__pycache__", ".venv"])]
        for p in all_py[:max_files]:
            rel_str = str(p.relative_to(repo_path)).replace("\\", "/")
            scored_files.append((1.0, rel_str, p, "test" in rel_str.lower()))

    for score, rel_str, file_path, is_test in scored_files[:max_files]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if len(content) > max_file_size:
                content = content[:max_file_size] + "\n... [TRUNCATED DUE TO SIZE] ..."

            results.append({
                "path": rel_str,
                "score": score,
                "content": content,
                "is_test": is_test,
            })
        except Exception:
            continue

    return results
