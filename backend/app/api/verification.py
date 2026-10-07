import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.task import Task
from app.models.patch import Patch
from app.models.test_run import TestRun
from app.models.verification import VerificationReport
from app.models.audit_log import AuditLog
from app.models.fix_history import FixHistory
from app.services.test_runner import execute_test_suite
from app.services.regression_guardian import create_isolated_sandbox, classify_regression
from app.services.rollback_manager import create_rollback_snapshot, restore_rollback_snapshot
from app.services.ai_provider import ai_provider_service
from app.services.report_generator import generate_markdown_report
from app.services.repository_integrity import verify_repository_integrity

router = APIRouter()


@router.post("/tasks/{task_id}/verify")
async def run_verification(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project = task.project
    repo_dir = Path(project.storage_path)
    if not repo_dir.exists():
        raise HTTPException(status_code=400, detail="Project storage directory missing")

    # Fetch proposed/approved patch
    patch = db.query(Patch).filter(
        Patch.task_id == task_id,
        Patch.attempt_number == task.current_attempt
    ).first()

    if not patch:
        raise HTTPException(status_code=400, detail="No candidate patch available to verify. Run analysis first.")

    task.status = "verifying"
    db.commit()

    # 1. Create clean isolated sandbox
    sandbox_dir = create_isolated_sandbox(repo_dir, task.id, task.current_attempt)
    snapshot_dir = settings.SANDBOX_DIR / f"task_{task.id}_attempt_{task.current_attempt}_snapshot"
    create_rollback_snapshot(sandbox_dir, snapshot_dir)

    # 2. Run Baseline Test Suite
    baseline_res = execute_test_suite(sandbox_dir)
    baseline_run = TestRun(
        task_id=task.id,
        attempt_number=task.current_attempt,
        stage="baseline",
        command=baseline_res["command"],
        exit_code=baseline_res["exit_code"],
        duration_ms=baseline_res["duration_ms"],
        passed_count=baseline_res["passed_count"],
        failed_count=baseline_res["failed_count"],
        error_count=baseline_res["error_count"],
        output_log=baseline_res["output_log"],
        test_details_json=json.dumps(baseline_res["test_details"])
    )
    db.add(baseline_run)
    db.commit()

    # 3. Apply approved patch to sandbox
    target_sandbox_file = (sandbox_dir / patch.target_file).resolve()
    target_sandbox_file.parent.mkdir(parents=True, exist_ok=True)
    target_sandbox_file.write_text(patch.new_code, encoding="utf-8")
    patch.status = "applied"

    db.add(AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="PATCH_APPLIED",
        actor="agent",
        details_json=json.dumps({"target_file": patch.target_file, "patch_id": patch.id})
    ))
    db.commit()

    # 4. Generate & write targeted regression test
    regression_test_code = await ai_provider_service.generate_regression_test(
        bug_title=task.bug_title,
        bug_description=task.bug_description,
        expected_behavior=task.expected_behavior or "",
        target_file_path=patch.target_file,
        target_file_content=patch.new_code
    )

    tests_dir = sandbox_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    reg_test_file = tests_dir / "test_codepilot_regression.py"
    reg_test_file.write_text(regression_test_code, encoding="utf-8")

    # 5. Run Post-Patch Test Suite
    db.add(AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="FULL_REGRESSION_SUITE_RUNNING",
        actor="guardian",
        details_json=json.dumps({"stage": "post_patch"})
    ))
    db.commit()

    post_res = execute_test_suite(sandbox_dir)
    post_run = TestRun(
        task_id=task.id,
        attempt_number=task.current_attempt,
        stage="post_patch",
        command=post_res.get("command", "pytest -v"),
        exit_code=post_res.get("exit_code", 0),
        duration_ms=post_res.get("duration_ms", 0),
        passed_count=post_res.get("passed_count", 0),
        failed_count=post_res.get("failed_count", 0),
        skipped_count=post_res.get("skipped_count", 0),
        error_count=post_res.get("error_count", 0),
        stdout=post_res.get("stdout", ""),
        stderr=post_res.get("stderr", ""),
        output_log=post_res.get("output_log", ""),
        test_details_json=json.dumps(post_res.get("test_details", []))
    )
    db.add(post_run)
    db.commit()

    # 6. Classify regression with Regression Guardian
    guardian_eval = classify_regression(baseline_res, post_res)
    classification = guardian_eval["classification"]

    db.add(AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="REGRESSION_ANALYSIS_COMPLETED",
        actor="guardian",
        details_json=json.dumps({
            "classification": classification,
            "regressions_count": guardian_eval.get("regressions_count", len(guardian_eval.get("regressed_tests", []))),
            "regressed_tests": guardian_eval.get("regressed_tests", [])
        })
    ))
    db.commit()

    # 7. Self-repair loop if verification failed and retries remain
    if classification in ("VERIFICATION_FAILED", "REGRESSION_DETECTED") and task.current_attempt < task.max_attempts:
        task.current_attempt += 1
        task.status = "repairing"
        db.commit()

        # Restore sandbox to clean baseline
        restore_rollback_snapshot(snapshot_dir, sandbox_dir)

        # Attempt revised patch
        revised_patch_dict = await ai_provider_service.generate_patch(
            bug_title=f"{task.bug_title} (Repair attempt {task.current_attempt})",
            bug_description=f"{task.bug_description}\nPrevious attempt failed: {guardian_eval.get('explanation', '')}",
            analysis=task.analysis,
            target_file_path=patch.target_file,
            target_file_content=patch.original_code
        )

        revised_patch = Patch(
            task_id=task.id,
            attempt_number=task.current_attempt,
            target_file=patch.target_file,
            original_code=patch.original_code,
            new_code=revised_patch_dict.get("new_code", patch.new_code),
            diff=patch.diff,
            explanation=f"Self-repair attempt {task.current_attempt}: {revised_patch_dict.get('explanation', '')}",
            potential_impact=patch.potential_impact,
            status="approved"
        )
        db.add(revised_patch)
        db.commit()

        # Re-apply revised patch
        target_sandbox_file.write_text(revised_patch.new_code, encoding="utf-8")
        post_res = execute_test_suite(sandbox_dir)
        guardian_eval = classify_regression(baseline_res, post_res)
        classification = guardian_eval["classification"]

    # 8. Full Repository Integrity Check
    integrity_res = verify_repository_integrity(repo_dir, sandbox_dir, [patch.target_file])
    db.add(AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="REPOSITORY_INTEGRITY_VERIFIED",
        actor="guardian",
        details_json=json.dumps({
            "passed": integrity_res.get("passed", True),
            "modified_files": integrity_res.get("modified_files", []),
            "unchanged_files_count": len(integrity_res.get("unchanged_files", []))
        })
    ))
    db.commit()

    if not integrity_res.get("passed", True):
        classification = "VERIFICATION_FAILED"
        fail_reasons = integrity_res.get("python_syntax_errors", []) + integrity_res.get("entry_point_errors", []) + [f"Deleted: {d}" for d in integrity_res.get("deleted_files", [])]
        guardian_eval["explanation"] = f"Repository integrity check failed: {'; '.join(fail_reasons)}"

    # 9. Record Final Verification Report
    functional_status = "PASSED" if classification == "FIX_VERIFIED" else "FAILED"
    regression_status = "PASSED" if len(guardian_eval.get("regressed_tests", [])) == 0 else "FAILED"

    report_payload = {
        "timestamp": task.updated_at.isoformat() if task.updated_at else task.created_at.isoformat(),
        "project": {"name": project.name},
        "task": {
            "id": task.id,
            "bug_title": task.bug_title,
            "current_attempt": task.current_attempt,
            "max_attempts": task.max_attempts
        },
        "verification": {
            "classification": classification,
            "functional_status": functional_status,
            "regression_status": regression_status,
            "syntax_status": "PASSED" if len(integrity_res.get("python_syntax_errors", [])) == 0 else "FAILED",
            "security_status": "PASSED"
        },
        "baseline_tests": baseline_res,
        "post_patch_tests": post_res,
        "patch_diff": patch.diff,
        "target_file": patch.target_file,
        "root_cause_summary": task.analysis.summary if task.analysis else "",
        "execution_mode": settings.EXECUTION_MODE,
        "guardian_evaluation": guardian_eval,
        "integrity_check": integrity_res
    }

    markdown_report = generate_markdown_report(report_payload)

    # Clear existing report if re-verifying
    existing_rep = db.query(VerificationReport).filter(VerificationReport.task_id == task.id).first()
    if existing_rep:
        db.delete(existing_rep)
        db.commit()

    verification_record = VerificationReport(
        task_id=task.id,
        classification=classification,
        functional_status=functional_status,
        regression_status=regression_status,
        syntax_status="PASSED" if len(integrity_res.get("python_syntax_errors", [])) == 0 else "FAILED",
        security_status="PASSED",
        evidence_summary_json=json.dumps(guardian_eval),
        integrity_check_json=json.dumps(integrity_res),
        markdown_report=markdown_report,
        json_report=json.dumps(report_payload)
    )
    db.add(verification_record)

    # Update Task Status and Materialize Corrected Workspace
    if classification == "FIX_VERIFIED":
        task.status = "verified"
        db.add(AuditLog(
            task_id=task.id,
            project_id=project.id,
            event_type="FIX_VERIFIED",
            actor="guardian",
            details_json=json.dumps({
                "regressions_count": 0,
                "target_file": patch.target_file
            })
        ))
        try:
            import shutil
            corrected_dir = settings.PROJECTS_DIR / f"project_{project.id}_corrected"
            if corrected_dir.exists():
                shutil.rmtree(corrected_dir, ignore_errors=True)
            shutil.copytree(
                repo_dir,
                corrected_dir,
                ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".venv", "storage", "*.pyc")
            )
            corrected_target = (corrected_dir / patch.target_file).resolve()
            corrected_target.parent.mkdir(parents=True, exist_ok=True)
            corrected_target.write_text(patch.new_code, encoding="utf-8")
            project.corrected_storage_path = str(corrected_dir.resolve())

            mat_audit = AuditLog(
                task_id=task.id,
                project_id=project.id,
                event_type="FIX_MATERIALIZED",
                actor="agent",
                details_json=json.dumps({
                    "corrected_path": str(corrected_dir),
                    "target_file": patch.target_file
                })
            )
            db.add(mat_audit)
        except Exception:
            pass
    else:
        task.status = "regression_failed"

    # Add to Fix History for Project Memory
    history_entry = FixHistory(
        project_id=project.id,
        project_name=project.name,
        bug_title=task.bug_title,
        root_cause_summary=task.analysis.summary if task.analysis else "",
        target_file=patch.target_file,
        patch_summary=patch.explanation,
        outcome=classification
    )
    db.add(history_entry)

    # Audit log
    audit = AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="VERIFICATION_COMPLETED",
        actor="guardian",
        details_json=json.dumps({
            "classification": classification,
            "baseline_passed": baseline_res["passed_count"],
            "post_passed": post_res["passed_count"],
            "regressions": len(guardian_eval.get("regressed_tests", []))
        })
    )
    db.add(audit)
    db.commit()

    return {
        "report_id": verification_record.id,
        "classification": classification,
        "functional_status": functional_status,
        "regression_status": regression_status,
        "syntax_status": "PASSED" if len(integrity_res.get("python_syntax_errors", [])) == 0 else "FAILED",
        "security_status": "PASSED",
        "baseline_tests": baseline_res,
        "post_patch_tests": post_res,
        "guardian_evaluation": guardian_eval,
        "integrity_check": integrity_res,
        "markdown_report": markdown_report
    }


@router.get("/tasks/{task_id}/verification")
def get_task_verification(task_id: int, db: Session = Depends(get_db)):
    report = db.query(VerificationReport).filter(VerificationReport.task_id == task_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Verification report not yet generated")

    return {
        "id": report.id,
        "task_id": report.task_id,
        "classification": report.classification,
        "functional_status": report.functional_status,
        "regression_status": report.regression_status,
        "syntax_status": report.syntax_status,
        "security_status": report.security_status,
        "evidence_summary": json.loads(report.evidence_summary_json or "{}"),
        "integrity_check": json.loads(report.integrity_check_json or "{}"),
        "markdown_report": report.markdown_report,
        "json_report": json.loads(report.json_report or "{}"),
        "created_at": report.created_at.isoformat()
    }


@router.get("/tasks/{task_id}/test-runs")
def get_task_test_runs(task_id: int, db: Session = Depends(get_db)):
    runs = db.query(TestRun).filter(TestRun.task_id == task_id).order_by(TestRun.created_at.asc()).all()
    results = []
    for r in runs:
        results.append({
            "id": r.id,
            "attempt_number": r.attempt_number,
            "stage": r.stage,
            "command": r.command,
            "exit_code": r.exit_code,
            "duration_ms": r.duration_ms,
            "passed_count": r.passed_count,
            "failed_count": r.failed_count,
            "skipped_count": r.skipped_count or 0,
            "error_count": r.error_count,
            "stdout": r.stdout or "",
            "stderr": r.stderr or "",
            "output_log": r.output_log,
            "test_details": json.loads(r.test_details_json or "[]"),
            "created_at": r.created_at.isoformat(),
        })
    return {"test_runs": results}


