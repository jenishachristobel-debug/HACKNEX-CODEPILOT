from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.fix_history import FixHistory

router = APIRouter()


@router.get("/history")
def get_fix_history(
    q: Optional[str] = Query(None, description="Search query"),
    project_id: Optional[int] = Query(None),
    outcome: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(FixHistory)

    if project_id:
        query = query.filter(FixHistory.project_id == project_id)
    if outcome:
        query = query.filter(FixHistory.outcome == outcome)
    if q:
        query = query.filter(
            (FixHistory.bug_title.ilike(f"%{q}%")) |
            (FixHistory.root_cause_summary.ilike(f"%{q}%")) |
            (FixHistory.project_name.ilike(f"%{q}%"))
        )

    records = query.order_by(FixHistory.created_at.desc()).all()
    results = []
    for h in records:
        results.append({
            "id": h.id,
            "project_id": h.project_id,
            "project_name": h.project_name,
            "bug_title": h.bug_title,
            "root_cause_summary": h.root_cause_summary,
            "target_file": h.target_file,
            "patch_summary": h.patch_summary,
            "outcome": h.outcome,
            "created_at": h.created_at.isoformat(),
        })

    return {"history": results}

