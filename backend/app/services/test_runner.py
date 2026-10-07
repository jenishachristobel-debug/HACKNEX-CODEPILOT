import os
import re
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from app.config import settings
from app.security.command_policy import validate_command_policy
from app.security.secret_redaction import redact_secrets


def parse_pytest_output(output: str) -> Dict[str, Any]:
    """
    Parses verbose pytest output to extract structured counts and test details.
    """
    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    test_details: List[Dict[str, Any]] = []

    # Pattern for verbose test lines: test_file.py::test_name PASSED / FAILED
    detail_pattern = re.compile(r"([a-zA-Z0-9_\-/\\]+\.py::[a-zA-Z0-9_\[\]\-]+)\s+(PASSED|FAILED|ERROR|SKIPPED)", re.IGNORECASE)
    for line in output.splitlines():
        m = detail_pattern.search(line)
        if m:
            test_name = m.group(1)
            status = m.group(2).upper()
            test_details.append({
                "name": test_name,
                "status": status,
                "duration_ms": 0,
                "message": ""
            })

    # Summary line pattern: e.g. "== 2 passed, 1 failed, 1 skipped in 0.05s =="
    summary_match = re.search(r"==+\s+(.*?)\s+in\s+([0-9\.]+)s\s+==+", output)
    if summary_match:
        summary_text = summary_match.group(1)
        passed_m = re.search(r"(\d+)\s+passed", summary_text)
        if passed_m:
            passed = int(passed_m.group(1))

        failed_m = re.search(r"(\d+)\s+failed", summary_text)
        if failed_m:
            failed = int(failed_m.group(1))

        skipped_m = re.search(r"(\d+)\s+skipped", summary_text)
        if skipped_m:
            skipped = int(skipped_m.group(1))

        error_m = re.search(r"(\d+)\s+error", summary_text)
        if error_m:
            errors = int(error_m.group(1))
    else:
        # Fallback counts from individual test list
        for t in test_details:
            if t["status"] == "PASSED":
                passed += 1
            elif t["status"] == "FAILED":
                failed += 1
            elif t["status"] == "SKIPPED":
                skipped += 1
            elif t["status"] == "ERROR":
                errors += 1

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
        "details": test_details
    }


def execute_test_suite(workspace_dir: Path, custom_args: List[str] = None) -> Dict[str, Any]:
    """
    Executes pytest inside the isolated workspace directory using safe subprocess.
    Enforces time limits, output limits, and command policy.
    """
    python_exe = sys.executable
    cmd = [python_exe, "-m", "pytest", "-v", "--tb=short"]
    if custom_args:
        cmd.extend(custom_args)

    validate_command_policy(cmd)

    # Set up safe, isolated environment
    env = os.environ.copy()
    python_paths = [str(workspace_dir.resolve())]
    try:
        for child in workspace_dir.iterdir():
            if child.is_dir() and not child.name.startswith(".") and child.name not in {"__pycache__", ".pytest_cache", ".venv", "storage"}:
                python_paths.append(str(child.resolve()))
    except Exception:
        pass
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    start_time = time.time()
    command_str = f"pytest -v"

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(workspace_dir.resolve()),
            capture_output=True,
            text=True,
            timeout=settings.TEST_TIMEOUT_SECONDS,
            env=env
        )
        duration_ms = int((time.time() - start_time) * 1000)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        combined_output = f"{stdout}\n{stderr}".strip()
        exit_code = proc.returncode

    except subprocess.TimeoutExpired as te:
        duration_ms = int((time.time() - start_time) * 1000)
        combined_output = f"Execution timed out after {settings.TEST_TIMEOUT_SECONDS}s."
        exit_code = -1
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        combined_output = f"Execution error: {str(e)}"
        exit_code = -2

    # Redact any accidental environment credentials
    clean_log = redact_secrets(combined_output)
    parsed = parse_pytest_output(clean_log)

    return {
        "command": command_str,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "passed_count": parsed["passed"],
        "failed_count": parsed["failed"],
        "skipped_count": parsed["skipped"],
        "error_count": parsed["errors"],
        "stdout": redact_secrets(stdout),
        "stderr": redact_secrets(stderr),
        "output_log": clean_log,
        "test_details": parsed["details"]
    }

