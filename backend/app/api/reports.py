import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.verification import VerificationReport
from app.models.task import Task

router = APIRouter()


@router.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(VerificationReport).order_by(VerificationReport.created_at.desc()).all()
    results = []
    for r in reports:
        task = r.task
        results.append({
            "id": r.id,
            "task_id": r.task_id,
            "project_name": task.project.name if (task and task.project) else "Unknown",
            "bug_title": task.bug_title if task else "Unknown",
            "classification": r.classification,
            "functional_status": r.functional_status,
            "regression_status": r.regression_status,
            "created_at": r.created_at.isoformat(),
        })
    return {"reports": results}


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    r = db.query(VerificationReport).filter(VerificationReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")

    task = r.task
    return {
        "id": r.id,
        "task_id": r.task_id,
        "project_name": task.project.name if (task and task.project) else "Unknown",
        "bug_title": task.bug_title if task else "Unknown",
        "classification": r.classification,
        "functional_status": r.functional_status,
        "regression_status": r.regression_status,
        "syntax_status": r.syntax_status,
        "security_status": r.security_status,
        "markdown_report": r.markdown_report,
        "json_report": json.loads(r.json_report or "{}"),
        "created_at": r.created_at.isoformat(),
    }


@router.get("/reports/{report_id}/export")
def export_report(
    report_id: int,
    format: str = Query("markdown", pattern="^(markdown|json)$"),
    db: Session = Depends(get_db)
):
    r = db.query(VerificationReport).filter(VerificationReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")

    filename = f"codepilot_report_task_{r.task_id}.{ 'md' if format == 'markdown' else 'json' }"

    if format == "json":
        return Response(
            content=r.json_report,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    return Response(
        content=r.markdown_report,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

