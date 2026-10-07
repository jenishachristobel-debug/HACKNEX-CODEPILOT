import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task import Task
from app.models.project import Project
from app.models.audit_log import AuditLog
from app.schemas.task import TaskCreate

router = APIRouter()


@router.post("/tasks")
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task = Task(
        project_id=payload.project_id,
        bug_title=payload.bug_title.strip(),
        bug_description=payload.bug_description.strip(),
        error_traceback=payload.error_traceback.strip() if payload.error_traceback else "",
        expected_behavior=payload.expected_behavior.strip() if payload.expected_behavior else "",
        actual_behavior=payload.actual_behavior.strip() if payload.actual_behavior else "",
        reproduction_steps=payload.reproduction_steps.strip() if payload.reproduction_steps else "",
        mode=payload.mode or "patch_and_verify",
        status="pending",
        current_attempt=1,
        max_attempts=2
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    audit = AuditLog(
        task_id=task.id,
        project_id=project.id,
        event_type="TASK_CREATED",
        actor="user",
        details_json=json.dumps({"bug_title": task.bug_title, "mode": task.mode})
    )
    db.add(audit)
    db.commit()

    return {
        "id": task.id,
        "project_id": task.project_id,
        "bug_title": task.bug_title,
        "bug_description": task.bug_description,
        "error_traceback": task.error_traceback,
        "expected_behavior": task.expected_behavior,
        "actual_behavior": task.actual_behavior,
        "reproduction_steps": task.reproduction_steps,
        "mode": task.mode,
        "status": task.status,
        "current_attempt": task.current_attempt,
        "max_attempts": task.max_attempts,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat() if task.updated_at else task.created_at.isoformat(),
    }


@router.get("/tasks")
def list_tasks(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    if status is not None:
        query = query.filter(Task.status == status)

    tasks = query.order_by(Task.created_at.desc()).all()
    results = []
    for t in tasks:
        results.append({
            "id": t.id,
            "project_id": t.project_id,
            "project_name": t.project.name if t.project else "Unknown",
            "bug_title": t.bug_title,
            "bug_description": t.bug_description,
            "mode": t.mode,
            "status": t.status,
            "current_attempt": t.current_attempt,
            "max_attempts": t.max_attempts,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat() if t.updated_at else t.created_at.isoformat(),
        })
    return {"tasks": results}


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    latest_patch = None
    if task.patches:
        lp = sorted(task.patches, key=lambda x: x.attempt_number, reverse=True)[0]
        latest_patch = {
            "id": lp.id,
            "attempt_number": lp.attempt_number,
            "target_file": lp.target_file,
            "status": lp.status,
            "diff": lp.diff,
            "explanation": lp.explanation,
        }

    verification = None
    if task.verification_report:
        verification = {
            "id": task.verification_report.id,
            "classification": task.verification_report.classification,
            "functional_status": task.verification_report.functional_status,
            "regression_status": task.verification_report.regression_status,
            "syntax_status": task.verification_report.syntax_status,
            "security_status": task.verification_report.security_status,
        }

    analysis_data = None
    if task.analysis:
        analysis_data = {
            "id": task.analysis.id,
            "summary": task.analysis.summary,
            "root_cause": task.analysis.root_cause,
            "call_path": task.analysis.call_path or "",
            "affected_files": json.loads(task.analysis.affected_files_json or "[]"),
            "affected_functions": json.loads(task.analysis.affected_functions_json or "[]"),
            "expected_behavior": task.analysis.expected_behavior or "",
            "actual_behavior": task.analysis.actual_behavior or "",
            "proposed_fix": task.analysis.proposed_fix or "",
        }

    return {
        "id": task.id,
        "project_id": task.project_id,
        "project_name": task.project.name if task.project else "Unknown",
        "bug_title": task.bug_title,
        "bug_description": task.bug_description,
        "error_traceback": task.error_traceback,
        "expected_behavior": task.expected_behavior,
        "actual_behavior": task.actual_behavior,
        "reproduction_steps": task.reproduction_steps,
        "mode": task.mode,
        "status": task.status,
        "current_attempt": task.current_attempt,
        "max_attempts": task.max_attempts,
        "latest_patch": latest_patch,
        "analysis": analysis_data,
        "verification": verification,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat() if task.updated_at else task.created_at.isoformat(),
    }


@router.get("/tasks/{task_id}/activity")
def get_task_activity(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    logs = db.query(AuditLog).filter(AuditLog.task_id == task_id).order_by(AuditLog.created_at.asc()).all()
    results = []
    for l in logs:
        details = {}
        try:
            details = json.loads(l.details_json or "{}")
        except Exception:
            pass

        results.append({
            "id": l.id,
            "event_type": l.event_type,
            "actor": l.actor,
            "details": details,
            "created_at": l.created_at.isoformat(),
        })

    return {"activity": results}

