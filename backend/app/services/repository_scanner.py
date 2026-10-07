import ast
import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set


def build_file_tree(directory: Path, current_path: Path = None) -> List[Dict[str, Any]]:
    """Builds a nested directory tree structure for UI exploration."""
    if current_path is None:
        current_path = directory

    nodes = []
    try:
        entries = sorted(os.scandir(current_path), key=lambda e: (not e.is_dir(), e.name.lower()))
    except Exception:
        return nodes

    for entry in entries:
        if entry.name.startswith(".") or entry.name in {"__pycache__", "node_modules", "storage", ".venv"}:
            continue

        rel_path = str(Path(entry.path).relative_to(directory)).replace("\\", "/")

        if entry.is_dir():
            children = build_file_tree(directory, Path(entry.path))
            nodes.append({
                "name": entry.name,
                "path": rel_path,
                "is_dir": True,
                "children": children,
            })
        else:
            nodes.append({
                "name": entry.name,
                "path": rel_path,
                "is_dir": False,
                "size": entry.stat().st_size,
            })

    return nodes


def parse_python_ast(file_path: Path) -> Dict[str, Any]:
    """
    Recursively analyzes a Python file using Python AST to extract:
    - module docstring
    - imports (modules, aliases, from-imports)
    - functions (standalone)
    - classes and methods
    - decorators
    - arguments
    - return statements
    - conditions (if expressions with operators)
    - loops (for, while)
    - exception handling (try, except, raise)
    - function calls
    - global variables
    - constants
    """
    info = {
        "module": "",
        "functions": [],
        "classes": [],
        "methods": [],
        "imports": [],
        "import_details": [],
        "decorators": [],
        "arguments": [],
        "return_statements": [],
        "conditions": [],
        "loops": [],
        "exception_handling": [],
        "function_calls": [],
        "global_variables": [],
        "constants": [],
        "syntax_error": None,
    }

    try:
        code = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(code, filename=str(file_path))
    except SyntaxError as se:
        info["syntax_error"] = f"Line {se.lineno}: {se.msg}"
        return info
    except Exception as e:
        info["syntax_error"] = str(e)
        return info

    info["module"] = ast.get_docstring(tree) or ""

    # Module-level assignments for global variables and constants
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    val_str = ""
                    try:
                        val_str = ast.unparse(node.value)
                    except Exception:
                        pass
                    info["global_variables"].append({"name": target.id, "value": val_str, "lineno": node.lineno})
                    if target.id.isupper():
                        info["constants"].append({"name": target.id, "value": val_str, "lineno": node.lineno})
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            val_str = ""
            if node.value:
                try:
                    val_str = ast.unparse(node.value)
                except Exception:
                    pass
            info["global_variables"].append({"name": node.target.id, "value": val_str, "lineno": node.lineno})
            if node.target.id.isupper():
                info["constants"].append({"name": node.target.id, "value": val_str, "lineno": node.lineno})

    def extract_func_details(fn_node: Any, is_method: bool = False, class_name: str = "") -> Dict[str, Any]:
        decorators = [ast.unparse(d) for d in fn_node.decorator_list]
        args = [a.arg for a in fn_node.args.args]
        returns = []
        conditions = []
        loops = []
        exceptions = []
        calls = []

        for child in ast.walk(fn_node):
            if isinstance(child, ast.Return) and child.value is not None:
                try:
                    returns.append(ast.unparse(child.value))
                except Exception:
                    pass
            elif isinstance(child, ast.If):
                try:
                    conditions.append(ast.unparse(child.test))
                except Exception:
                    pass
            elif isinstance(child, (ast.For, ast.While)):
                try:
                    loops.append(ast.unparse(getattr(child, "target", child)))
                except Exception:
                    loops.append(type(child).__name__)
            elif isinstance(child, ast.Try):
                for h in child.handlers:
                    exc_name = ast.unparse(h.type) if h.type else "Exception"
                    exceptions.append(f"catch {exc_name}")
            elif isinstance(child, ast.Raise):
                exc_raised = ast.unparse(child.exc) if child.exc else "re-raise"
                exceptions.append(f"raise {exc_raised}")
            elif isinstance(child, ast.Call):
                try:
                    calls.append(ast.unparse(child.func))
                except Exception:
                    pass

        return {
            "name": fn_node.name,
            "qualified_name": f"{class_name}.{fn_node.name}" if class_name else fn_node.name,
            "lineno": fn_node.lineno,
            "end_lineno": getattr(fn_node, "end_lineno", fn_node.lineno),
            "is_async": isinstance(fn_node, ast.AsyncFunctionDef),
            "is_method": is_method,
            "class_name": class_name,
            "args": args,
            "decorators": decorators,
            "return_statements": returns,
            "conditions": conditions,
            "loops": loops,
            "exception_handling": exceptions,
            "function_calls": calls,
            "docstring": ast.get_docstring(fn_node) or "",
        }

    # Extract top-level functions and classes
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            f_detail = extract_func_details(node, is_method=False)
            info["functions"].append(f_detail)
            info["decorators"].extend(f_detail["decorators"])
            info["arguments"].extend(f_detail["args"])
            info["return_statements"].extend(f_detail["return_statements"])
            info["conditions"].extend(f_detail["conditions"])
            info["loops"].extend(f_detail["loops"])
            info["exception_handling"].extend(f_detail["exception_handling"])
            info["function_calls"].extend(f_detail["function_calls"])

        elif isinstance(node, ast.ClassDef):
            class_methods = []
            c_decorators = [ast.unparse(d) for d in node.decorator_list]
            bases = [ast.unparse(b) for b in node.bases]

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_detail = extract_func_details(item, is_method=True, class_name=node.name)
                    class_methods.append(m_detail)
                    info["methods"].append(m_detail)
                    info["decorators"].extend(m_detail["decorators"])
                    info["arguments"].extend(m_detail["args"])
                    info["return_statements"].extend(m_detail["return_statements"])
                    info["conditions"].extend(m_detail["conditions"])
                    info["loops"].extend(m_detail["loops"])
                    info["exception_handling"].extend(m_detail["exception_handling"])
                    info["function_calls"].extend(m_detail["function_calls"])

            info["classes"].append({
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
                "bases": bases,
                "decorators": c_decorators,
                "methods": class_methods,
                "docstring": ast.get_docstring(node) or "",
            })

    # Extract all imports across the file
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                info["imports"].append(alias.name)
                info["import_details"].append({
                    "module": alias.name,
                    "name": alias.name,
                    "asname": alias.asname,
                    "is_from": False,
                    "lineno": node.lineno
                })
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                full_name = f"{mod}.{alias.name}" if mod else alias.name
                info["imports"].append(full_name)
                info["import_details"].append({
                    "module": mod,
                    "name": alias.name,
                    "asname": alias.asname,
                    "is_from": True,
                    "level": node.level,
                    "lineno": node.lineno
                })

    return info


def build_repository_inventory(repo_dir: Path) -> List[Dict[str, Any]]:
    """
    Recursively scans the entire repository to build a complete inventory of:
    - every source file
    - every test file
    - every configuration file
    - every documentation file
    - file sizes, types, and programming languages
    """
    inventory: List[Dict[str, Any]] = []
    repo_path = repo_dir.resolve()

    extension_lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".ini": "INI",
        ".cfg": "INI",
        ".md": "Markdown",
        ".txt": "Text",
        ".rst": "reStructuredText",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".java": "Java",
        ".kt": "Kotlin",
        ".go": "Go",
        ".rs": "Rust",
        ".c": "C",
        ".cpp": "C++",
        ".h": "C/C++ Header",
        ".sh": "Shell",
        ".bat": "Batch",
        ".ps1": "PowerShell",
    }

    config_names = {
        "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "pipfile", "poetry.lock",
        "package.json", "package-lock.json", "tsconfig.json", "vite.config.ts", "vite.config.js",
        "pytest.ini", "tox.ini", ".editorconfig", "dockerfile", "docker-compose.yml"
    }

    for root, _, files in os.walk(repo_path):
        rel_root = Path(root).relative_to(repo_path)
        parts = rel_root.parts

        # Skip internal directories
        if any(p.startswith(".") or p in {"__pycache__", "storage", ".venv", "node_modules", ".pytest_cache"} for p in parts):
            continue

        for f in sorted(files):
            file_path = Path(root) / f
            rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
            f_lower = f.lower()
            ext = file_path.suffix.lower()

            size = file_path.stat().st_size
            lang = extension_lang_map.get(ext, "Other")

            # Determine file type
            is_test = (
                f_lower.startswith("test_") or
                f_lower.endswith("_test.py") or
                f_lower.endswith(".test.js") or
                f_lower.endswith(".spec.ts") or
                "tests/" in rel_path or
                "test/" in rel_path or
                "spec/" in rel_path
            )

            is_package_meta = f_lower in {
                "requirements.txt", "pyproject.toml", "setup.py", "pipfile", "poetry.lock",
                "package.json", "package-lock.json"
            }

            is_config = f_lower in config_names or ext in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
            is_doc = ext in {".md", ".txt", ".rst"} or f_lower.startswith("readme") or "docs/" in rel_path

            if is_test:
                file_type = "test"
            elif is_package_meta:
                file_type = "package_metadata"
            elif is_config:
                file_type = "config"
            elif is_doc:
                file_type = "documentation"
            elif ext in {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".c", ".cpp"}:
                file_type = "source"
            else:
                file_type = "other"

            # Entry point heuristic
            is_entry_point = False
            if ext == ".py":
                if f_lower in {"main.py", "app.py", "api.py", "server.py", "manage.py", "cli.py"}:
                    is_entry_point = True

            inventory.append({
                "path": rel_path,
                "name": f,
                "size": size,
                "file_type": file_type,
                "language": lang,
                "extension": ext,
                "is_test": is_test,
                "is_entry_point": is_entry_point
            })

    return inventory


def detect_test_framework(repo_dir: Path, inventory: List[Dict[str, Any]]) -> str:
    """Detects the test framework configured for the repository."""
    repo_path = repo_dir.resolve()
    file_names = {item["name"].lower() for item in inventory}

    if "pytest.ini" in file_names or (repo_path / "pytest.ini").exists():
        return "pytest"

    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8", errors="replace")
            if "tool.pytest" in content:
                return "pytest"
        except Exception:
            pass

    reqs = repo_path / "requirements.txt"
    if reqs.exists():
        try:
            content = reqs.read_text(encoding="utf-8", errors="replace")
            if "pytest" in content:
                return "pytest"
        except Exception:
            pass

    # Inspect test files for unittest vs pytest imports
    for item in inventory:
        if item["is_test"] and item["extension"] == ".py":
            try:
                content = (repo_path / item["path"]).read_text(encoding="utf-8", errors="replace")
                if "import pytest" in content or "from pytest" in content:
                    return "pytest"
                if "import unittest" in content or "TestCase" in content:
                    return "unittest"
            except Exception:
                pass

    return "pytest"


def detect_package_manager(repo_dir: Path, inventory: List[Dict[str, Any]]) -> str:
    """Detects the package manager used by the repository."""
    names = {item["name"].lower() for item in inventory}

    if "poetry.lock" in names or "poetry" in names:
        return "poetry"
    if "pipfile" in names or "pipfile.lock" in names:
        return "pipenv"
    if "requirements.txt" in names or "setup.py" in names:
        return "pip"
    if "package-lock.json" in names:
        return "npm"
    if "yarn.lock" in names:
        return "yarn"
    if "pnpm-lock.yaml" in names:
        return "pnpm"
    if "package.json" in names:
        return "npm"

    return "pip"


def generate_repository_manifest(
    repo_name: str,
    inventory: List[Dict[str, Any]],
    symbols: Dict[str, Any],
    repo_dir: Path
) -> Dict[str, Any]:
    """
    Creates an internal repository manifest matching Section 4.
    """
    languages_set = {item["language"] for item in inventory if item["language"] not in {"Other", "Text"}}
    languages = sorted(list(languages_set)) if languages_set else ["Python"]

    source_files = [item for item in inventory if item["file_type"] == "source"]
    test_files = [item for item in inventory if item["file_type"] == "test"]
    config_files = [item for item in inventory if item["file_type"] in {"config", "package_metadata"}]
    doc_files = [item for item in inventory if item["file_type"] == "documentation"]

    entry_points = [item["path"] for item in inventory if item.get("is_entry_point")]
    if not entry_points and source_files:
        # Fallback entry point to first non-test python file
        entry_points = [source_files[0]["path"]]

    test_framework = detect_test_framework(repo_dir, inventory)
    package_manager = detect_package_manager(repo_dir, inventory)

    return {
        "repository": repo_name or repo_dir.name,
        "languages": languages,
        "files": len(inventory),
        "source_files": len(source_files),
        "test_files": len(test_files),
        "config_files": len(config_files),
        "documentation_files": len(doc_files),
        "entry_points": entry_points,
        "test_framework": test_framework,
        "package_manager": package_manager
    }


def build_dependency_graph(
    repo_dir: Path,
    symbols: Dict[str, Any],
    inventory: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Builds a repository import and call dependency graph matching Section 6.
    Traces modules, imports, function calls, and reverse dependencies across files.
    """
    # 1. Map python module names to relative file paths
    module_to_file: Dict[str, str] = {}
    for item in inventory:
        if item["extension"] == ".py":
            rel = item["path"]
            mod_simple = Path(rel).stem
            mod_full = rel.replace("/", ".").removesuffix(".py")
            module_to_file[mod_simple] = rel
            module_to_file[mod_full] = rel

    nodes = []
    for item in inventory:
        nodes.append({
            "id": item["path"],
            "name": item["name"],
            "file_type": item["file_type"],
            "language": item["language"],
            "is_entry_point": item.get("is_entry_point", False),
            "is_test": item.get("is_test", False),
        })

    edges = []
    reverse_deps: Dict[str, List[str]] = {item["path"]: [] for item in inventory}
    call_graph: Dict[str, List[Dict[str, str]]] = {}
    call_chains: List[List[str]] = []

    # 2. Build import edges and function call linkages
    for rel_path, ast_data in symbols.items():
        if not ast_data or ast_data.get("syntax_error"):
            continue

        imported_modules_map: Dict[str, str] = {}  # symbol_or_alias -> target_file

        for imp in ast_data.get("import_details", []):
            mod_name = imp.get("module") or imp.get("name")
            target_rel = module_to_file.get(mod_name) or module_to_file.get(mod_name.split(".")[-1])

            if target_rel and target_rel != rel_path:
                symbol_name = imp.get("name")
                edges.append({
                    "from": rel_path,
                    "to": target_rel,
                    "symbol": symbol_name,
                    "type": "import"
                })

                if rel_path not in reverse_deps[target_rel]:
                    reverse_deps[target_rel].append(rel_path)

                if imp.get("is_from"):
                    imported_modules_map[symbol_name] = target_rel

        # Function calls mapping
        all_funcs = ast_data.get("functions", []) + ast_data.get("methods", [])
        for f in all_funcs:
            caller_qual = f"{rel_path}::{f['name']}"
            call_graph[caller_qual] = []

            for call_name in f.get("function_calls", []):
                # Call directly matches an imported symbol from another file
                callee_file = imported_modules_map.get(call_name)
                if callee_file:
                    callee_qual = f"{callee_file}::{call_name}"
                    call_graph[caller_qual].append({
                        "file": callee_file,
                        "function": call_name,
                        "qualified": callee_qual
                    })
                    call_chains.append([caller_qual, callee_qual])

    return {
        "nodes": nodes,
        "edges": edges,
        "reverse_dependencies": reverse_deps,
        "call_graph": call_graph,
        "call_chains": call_chains
    }


def parse_bug_report(repo_dir: Path) -> Optional[Dict[str, Any]]:
    """Finds and parses any BUG_REPORT.md or documented bug report in the repository."""
    candidates = list(repo_dir.glob("BUG_REPORT.md")) or \
                 list(repo_dir.glob("bug_report.md")) or \
                 list(repo_dir.glob("*/BUG_REPORT.md")) or \
                 list(repo_dir.glob("*bug*.md"))

    if not candidates:
        return None

    report_file = candidates[0]
    try:
        content = report_file.read_text(encoding="utf-8", errors="replace").strip()
        rel_path = str(report_file.relative_to(repo_dir)).replace("\\", "/")

        title = "Documented Repository Bug"
        body_lines = []
        repro_cmd = ""

        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and title == "Documented Repository Bug":
                title = stripped[2:].strip()
            elif "`pytest" in stripped or "pytest" in stripped:
                repro_cmd = stripped
                body_lines.append(stripped)
            elif stripped:
                body_lines.append(stripped)

        description = "\n".join(body_lines)

        return {
            "has_bug_report": True,
            "path": rel_path,
            "title": title,
            "description": description,
            "reproduction_command": repro_cmd,
            "raw_content": content,
            "suggested_task": {
                "bug_title": title,
                "bug_description": description,
                "reproduction_steps": repro_cmd or "Run pytest -q to reproduce.",
                "expected_behavior": "Satisfy documented requirements and pass all unit tests.",
                "actual_behavior": "Unit test suite fails due to edge case or boundary logic."
            }
        }
    except Exception:
        return None


def detect_repo_language(repo_dir: Path) -> str:
    """Detects the primary language or framework of a repository."""
    counts = {
        "JavaScript/TypeScript": 0,
        "Python": 0,
        "Java/Kotlin": 0,
        "Go": 0,
        "Rust": 0,
        "C/C++": 0,
        "HTML/CSS": 0,
    }

    repo_path = repo_dir.resolve()
    for root, _, files in os.walk(repo_path):
        rel_root = Path(root).relative_to(repo_path)
        parts = rel_root.parts
        if any(p.startswith(".") or p in {"__pycache__", "storage", ".venv", "node_modules"} for p in parts):
            continue

        for f in files:
            f_lower = f.lower()
            if f_lower in {"package.json", "tsconfig.json", "vite.config.ts", "vite.config.js"}:
                counts["JavaScript/TypeScript"] += 5
            elif f_lower.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
                counts["JavaScript/TypeScript"] += 1
            elif f_lower in {"requirements.txt", "pyproject.toml", "setup.py", "pipfile"}:
                counts["Python"] += 5
            elif f_lower.endswith(".py"):
                counts["Python"] += 1
            elif f_lower in {"pom.xml", "build.gradle"}:
                counts["Java/Kotlin"] += 5
            elif f_lower.endswith((".java", ".kt")):
                counts["Java/Kotlin"] += 1
            elif f_lower == "go.mod" or f_lower.endswith(".go"):
                counts["Go"] += 2
            elif f_lower == "cargo.toml" or f_lower.endswith(".rs"):
                counts["Rust"] += 2
            elif f_lower in {"cmakelists.txt", "makefile"} or f_lower.endswith((".c", ".cpp", ".cc", ".h", ".hpp")):
                counts["C/C++"] += 1
            elif f_lower.endswith((".html", ".css", ".scss")):
                counts["HTML/CSS"] += 1

    sorted_langs = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    top_lang, top_count = sorted_langs[0]
    if top_count > 0:
        return top_lang
    return "Unknown (non-Python)"


def scan_repository(repo_dir: Path, repo_name: str = "") -> Dict[str, Any]:
    """
    Performs full repository discovery, AST analysis, manifest generation,
    and dependency graph construction for the entire uploaded repository.
    """
    repo_path = repo_dir.resolve()
    inventory = build_repository_inventory(repo_path)

    total_files = len(inventory)
    python_files = sum(1 for item in inventory if item["extension"] == ".py")
    test_files = sum(1 for item in inventory if item["is_test"])
    syntax_errors = 0
    symbols: Dict[str, Any] = {}
    dependencies: List[str] = []

    # Parse dependencies from requirements.txt
    req_candidates = list(repo_path.glob("requirements.txt")) or list(repo_path.glob("*/requirements.txt"))
    if req_candidates:
        try:
            for line in req_candidates[0].read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    dependencies.append(line)
        except Exception:
            pass

    # Perform AST analysis on all Python files
    for item in inventory:
        if item["extension"] == ".py":
            file_path = repo_path / item["path"]
            ast_info = parse_python_ast(file_path)
            if ast_info["syntax_error"]:
                syntax_errors += 1
            symbols[item["path"]] = ast_info

    file_tree = build_file_tree(repo_path)
    bug_report = parse_bug_report(repo_path)
    manifest = generate_repository_manifest(repo_name or repo_dir.name, inventory, symbols, repo_path)
    dependency_graph = build_dependency_graph(repo_path, symbols, inventory)

    return {
        "total_files": total_files,
        "python_files": python_files,
        "test_files": test_files,
        "syntax_errors_count": syntax_errors,
        "dependencies": dependencies,
        "file_tree": file_tree,
        "symbols": symbols,
        "bug_report": bug_report,
        "inventory": inventory,
        "manifest": manifest,
        "dependency_graph": dependency_graph
    }
