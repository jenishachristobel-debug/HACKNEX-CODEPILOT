import shutil
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from app.config import settings
from app.services.test_runner import execute_test_suite


def classify_regression(
    baseline_run: Dict[str, Any],
    post_patch_run: Dict[str, Any],
    new_regression_passed: bool = True
) -> Dict[str, Any]:
    """
    Compares baseline and post-patch test executions to determine regression status:
    - FIX_VERIFIED: Bug repaired, and 0 regressions introduced.
    - REGRESSION_DETECTED: Previously passing baseline test now fails.
    - VERIFICATION_FAILED: Post-patch tests fail or test suite fails to compile.
    - PARTIALLY_VERIFIED: Some checks pass, but regression test inconclusive.
    - NOT EXECUTED: If execution could not proceed.
    """
    if baseline_run.get("exit_code") in (-1, -2) or post_patch_run.get("exit_code") in (-1, -2):
        return {
            "classification": "NOT EXECUTED",
            "explanation": "Execution timed out or subprocess failed to initialize."
        }

    baseline_details = {t["name"]: t["status"] for t in baseline_run.get("test_details", [])}
    post_details = {t["name"]: t["status"] for t in post_patch_run.get("test_details", [])}

    # Find previously passing tests that now fail
    regressed_tests = []
    for test_name, status in baseline_details.items():
        if status == "PASSED" and post_details.get(test_name) in ("FAILED", "ERROR"):
            regressed_tests.append(test_name)

    # Find newly passing tests
    newly_passing = []
    for test_name, status in post_details.items():
        if status == "PASSED" and baseline_details.get(test_name) in ("FAILED", "ERROR"):
            newly_passing.append(test_name)

    # Remaining failing tests
    still_failing = []
    for test_name, status in post_details.items():
        if status in ("FAILED", "ERROR") and baseline_details.get(test_name) in ("FAILED", "ERROR"):
            still_failing.append(test_name)

    regressions_count = len(regressed_tests)

    if regressed_tests:
        return {
            "classification": "REGRESSION_DETECTED",
            "regressions_count": regressions_count,
            "regressed_tests": regressed_tests,
            "newly_passing": newly_passing,
            "still_failing": still_failing,
            "explanation": f"Regression detected: {regressions_count} previously passing test(s) failed after applying patch."
        }

    if post_patch_run.get("failed_count", 0) == 0 and post_patch_run.get("error_count", 0) == 0 and new_regression_passed:
        return {
            "classification": "FIX_VERIFIED",
            "regressions_count": 0,
            "regressed_tests": [],
            "newly_passing": newly_passing,
            "still_failing": [],
            "explanation": "Fix verified: All tests passed with zero regressions in baseline suite."
        }

    if post_patch_run.get("failed_count", 0) > 0 or post_patch_run.get("error_count", 0) > 0:
        return {
            "classification": "VERIFICATION_FAILED",
            "regressions_count": regressions_count,
            "regressed_tests": regressed_tests,
            "newly_passing": newly_passing,
            "still_failing": still_failing,
            "explanation": f"Post-patch verification failed: {post_patch_run.get('failed_count', 0)} test(s) failed, {post_patch_run.get('error_count', 0)} error(s)."
        }

    return {
        "classification": "PARTIALLY_VERIFIED",
        "regressions_count": regressions_count,
        "regressed_tests": [],
        "newly_passing": newly_passing,
        "still_failing": still_failing,
        "explanation": "Checks completed but verification remains partial."
    }


def create_isolated_sandbox(project_dir: Path, task_id: int, attempt: int = 1) -> Path:
    """Creates a clean, isolated task sandbox workspace clone."""
    sandbox_path = settings.SANDBOX_DIR / f"task_{task_id}_attempt_{attempt}"
    if sandbox_path.exists():
        shutil.rmtree(sandbox_path, ignore_errors=True)

    shutil.copytree(
        project_dir,
        sandbox_path,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".venv", "storage")
    )
    return sandbox_path

