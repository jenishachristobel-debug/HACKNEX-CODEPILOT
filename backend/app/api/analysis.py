import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task import Task
from app.models.analysis import AnalysisResult
from app.models.patch import Patch
from app.models.test_run import TestRun
from app.models.audit_log import AuditLog
from app.services.context_retriever import retrieve_relevant_context
from app.services.ai_provider import ai_provider_service
from app.services.patch_validator import generate_unified_diff, validate_patch_candidate
from app.services.impact_analyzer import analyze_change_impact
from app.services.test_runner import execute_test_suite

router = APIRouter()


@router.post("/tasks/{task_id}/analyze")
async def analyze_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project = task.project
    repo_dir = Path(project.storage_path)
    if not repo_dir.exists():
        raise HTTPException(status_code=400, detail="Project storage directory missing")

    task.status = "investigating"
    db.commit()

    # 1. BASELINE TEST RUN (Pre-patch test execution recorded in MySQL)
    db.add(AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="BASELINE_TESTS_RUNNING",
        actor="agent",
        details_json=json.dumps({"stage": "baseline", "repo": project.name})
    ))
    db.commit()

    baseline_res = execute_test_suite(repo_dir)

    # Save or update baseline TestRun record
    db.query(TestRun).filter(
        TestRun.task_id == task_id,
        TestRun.attempt_number == task.current_attempt,
        TestRun.stage == "baseline"
    ).delete()

    baseline_run = TestRun(
        task_id=task.id,
        attempt_number=task.current_attempt,
        stage="baseline",
        command=baseline_res.get("command", "pytest -v"),
        exit_code=baseline_res.get("exit_code", 0),
        duration_ms=baseline_res.get("duration_ms", 0),
        passed_count=baseline_res.get("passed_count", 0),
        failed_count=baseline_res.get("failed_count", 0),
        skipped_count=baseline_res.get("skipped_count", 0),
        error_count=baseline_res.get("error_count", 0),
        stdout=baseline_res.get("stdout", ""),
        stderr=baseline_res.get("stderr", ""),
        output_log=baseline_res.get("output_log", ""),
        test_details_json=json.dumps(baseline_res.get("test_details", []))
    )
    db.add(baseline_run)

    db.add(AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="BASELINE_TESTS_COMPLETED",
        actor="agent",
        details_json=json.dumps({
            "passed": baseline_res.get("passed_count", 0),
            "failed": baseline_res.get("failed_count", 0),
            "skipped": baseline_res.get("skipped_count", 0),
            "duration_ms": baseline_res.get("duration_ms", 0)
        })
    ))
    db.commit()

    # 2. BUG ANALYSIS & CONTEXT RETRIEVAL
    db.add(AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="ANALYZING_BUG",
        actor="agent",
        details_json=json.dumps({
            "bug_title": task.bug_title,
            "bug_description": task.bug_description
        })
    ))
    db.commit()

    symbols = {}
    if project.scan and project.scan.symbols_json:
        try:
            symbols = json.loads(project.scan.symbols_json)
        except Exception:
            pass

    context_files = retrieve_relevant_context(
        repo_dir=repo_dir,
        bug_title=task.bug_title,
        bug_description=task.bug_description,
        error_traceback=task.error_traceback or "",
        symbols=symbols
    )

    # 3. ROOT CAUSE INVESTIGATION
    root_cause_struct = await ai_provider_service.analyze_bug(
        bug_title=task.bug_title,
        bug_description=task.bug_description,
        error_traceback=task.error_traceback or "",
        relevant_files=context_files
    )

    db.add(AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="ROOT_CAUSE_IDENTIFIED",
        actor="agent",
        details_json=json.dumps({
            "root_cause": root_cause_struct.root_cause,
            "call_path": root_cause_struct.call_path,
            "affected_files": root_cause_struct.affected_files,
            "affected_functions": root_cause_struct.affected_functions
        })
    ))

    # Save or update AnalysisResult
    existing_analysis = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if existing_analysis:
        db.delete(existing_analysis)
        db.commit()

    analysis_record = AnalysisResult(
        task_id=task.id,
        summary=root_cause_struct.summary,
        root_cause=root_cause_struct.root_cause,
        affected_files_json=json.dumps(root_cause_struct.affected_files),
        affected_functions_json=json.dumps(root_cause_struct.affected_functions),
        evidence_json=json.dumps(root_cause_struct.evidence),
        proposed_plan_json=json.dumps(root_cause_struct.proposed_plan),
        potential_side_effects_json=json.dumps(root_cause_struct.potential_side_effects),
        uncertainties_json=json.dumps(root_cause_struct.uncertainties),
        call_path=root_cause_struct.call_path or "",
        expected_behavior=root_cause_struct.expected_behavior or "",
        actual_behavior=root_cause_struct.actual_behavior or "",
        proposed_fix=root_cause_struct.proposed_fix or "",
        is_llm_generated=ai_provider_service.is_configured()
    )
    db.add(analysis_record)

    # 4. PATCH SYNTHESIS
    target_rel = root_cause_struct.affected_files[0] if root_cause_struct.affected_files else "app.py"
    target_path = (repo_dir / target_rel).resolve()
    orig_code = ""
    if target_path.exists():
        orig_code = target_path.read_text(encoding="utf-8", errors="replace")

    db.add(AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="GENERATING_PATCH",
        actor="agent",
        details_json=json.dumps({
            "target_file": target_rel
        })
    ))

    patch_dict = await ai_provider_service.generate_patch(
        bug_title=task.bug_title,
        bug_description=task.bug_description,
        analysis=root_cause_struct,
        target_file_path=target_rel,
        target_file_content=orig_code
    )

    new_code = patch_dict.get("new_code", orig_code)
    unified_diff = generate_unified_diff(orig_code, new_code, target_rel)
    impact_data = analyze_change_impact(repo_dir, target_rel, orig_code, new_code)

    # Clear prior patches for this attempt if any
    db.query(Patch).filter(Patch.task_id == task_id, Patch.attempt_number == task.current_attempt).delete()

    patch_record = Patch(
        task_id=task.id,
        attempt_number=task.current_attempt,
        target_file=target_rel,
        original_code=orig_code,
        new_code=new_code,
        diff=unified_diff,
        explanation=patch_dict.get("explanation", "Targeted minimal patch applied."),
        potential_impact=impact_data.get("blast_radius_summary", "Minimal blast radius"),
        status="proposed"
    )
    db.add(patch_record)

    task.status = "patch_ready"

    # Audit log
    audit = AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="ANALYSIS_COMPLETED",
        actor="agent",
        details_json=json.dumps({
            "root_cause": root_cause_struct.root_cause,
            "target_file": target_rel,
            "call_path": root_cause_struct.call_path,
            "is_llm": ai_provider_service.is_configured()
        })
    )
    db.add(audit)
    db.commit()

    return {
        "analysis": {
            "id": analysis_record.id,
            "summary": analysis_record.summary,
            "root_cause": analysis_record.root_cause,
            "affected_files": root_cause_struct.affected_files,
            "affected_functions": root_cause_struct.affected_functions,
            "call_path": root_cause_struct.call_path,
            "evidence": root_cause_struct.evidence,
            "proposed_plan": root_cause_struct.proposed_plan,
            "potential_side_effects": root_cause_struct.potential_side_effects,
            "uncertainties": root_cause_struct.uncertainties,
            "expected_behavior": root_cause_struct.expected_behavior,
            "actual_behavior": root_cause_struct.actual_behavior,
            "proposed_fix": root_cause_struct.proposed_fix,
            "is_llm_generated": analysis_record.is_llm_generated,
        },
        "patch": {
            "id": patch_record.id,
            "target_file": patch_record.target_file,
            "diff": patch_record.diff,
            "explanation": patch_record.explanation,
            "potential_impact": patch_record.potential_impact,
            "status": patch_record.status,
            "impact_analysis": impact_data
        }
    }


@router.get("/tasks/{task_id}/analysis")
def get_analysis(task_id: int, db: Session = Depends(get_db)):
    analysis = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found for this task")

    return {
        "id": analysis.id,
        "task_id": analysis.task_id,
        "summary": analysis.summary,
        "root_cause": analysis.root_cause,
        "affected_files": json.loads(analysis.affected_files_json or "[]"),
        "affected_functions": json.loads(analysis.affected_functions_json or "[]"),
        "call_path": analysis.call_path or "",
        "evidence": json.loads(analysis.evidence_json or "[]"),
        "proposed_plan": json.loads(analysis.proposed_plan_json or "[]"),
        "potential_side_effects": json.loads(analysis.potential_side_effects_json or "[]"),
        "uncertainties": json.loads(analysis.uncertainties_json or "[]"),
        "expected_behavior": analysis.expected_behavior or "",
        "actual_behavior": analysis.actual_behavior or "",
        "proposed_fix": analysis.proposed_fix or "",
        "is_llm_generated": analysis.is_llm_generated,
        "created_at": analysis.created_at.isoformat()
    }

