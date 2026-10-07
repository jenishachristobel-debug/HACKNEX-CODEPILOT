import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.patch import Patch
from app.models.task import Task
from app.models.project import Project
from app.models.audit_log import AuditLog
from app.schemas.patch import PatchValidateRequest, PatchResponse
from app.security.path_validator import validate_safe_path
from app.services.patch_validator import validate_patch_candidate, generate_unified_diff
from app.services.rollback_manager import create_rollback_snapshot, restore_rollback_snapshot
from app.services.regression_guardian import create_isolated_sandbox

router = APIRouter()


@router.post("/patches/validate")
def validate_patch(payload: PatchValidateRequest, db: Session = Depends(get_db)):
    """
    Validates a patch candidate against workspace constraints.
    Rejects path traversal, escapes, or malformed Python syntax.
    """
    target_file = payload.patch.target_file
    new_code = payload.patch.new_code

    # 1. Early traversal check
    clean_target = target_file.strip().replace("\\", "/")
    if ".." in clean_target.split("/") or clean_target.startswith("/") or ":" in clean_target:
        raise HTTPException(status_code=400, detail="Invalid patch target: path traversal detected")

    project = db.query(Project).filter(Project.id == payload.project_id).first()
    base_dir = Path(project.storage_path) if (project and project.storage_path) else settings.PROJECTS_DIR

    # 2. Check path safety against base directory
    try:
        validate_safe_path(target_file, base_dir)
    except HTTPException as he:
        raise HTTPException(status_code=400, detail=f"Invalid patch path: {he.detail}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid patch: {str(e)}")

    # 3. Validate Python syntax
    is_valid, error_msg = validate_patch_candidate(base_dir, target_file, new_code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid patch content: {error_msg}")

    return {
        "valid": True,
        "target_file": target_file,
        "message": "Patch validated successfully"
    }


@router.get("/tasks/{task_id}/patches")
def get_task_patches(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    patches = db.query(Patch).filter(Patch.task_id == task_id).order_by(Patch.attempt_number.desc()).all()
    results = []
    for p in patches:
        results.append({
            "id": p.id,
            "task_id": p.task_id,
            "attempt_number": p.attempt_number,
            "target_file": p.target_file,
            "original_code": p.original_code,
            "new_code": p.new_code,
            "diff": p.diff,
            "explanation": p.explanation,
            "potential_impact": p.potential_impact,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
        })
    return {"patches": results}


@router.get("/patches/{patch_id}")
def get_patch_detail(patch_id: int, db: Session = Depends(get_db)):
    patch = db.query(Patch).filter(Patch.id == patch_id).first()
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")

    return {
        "id": patch.id,
        "task_id": patch.task_id,
        "attempt_number": patch.attempt_number,
        "target_file": patch.target_file,
        "original_code": patch.original_code,
        "new_code": patch.new_code,
        "diff": patch.diff,
        "explanation": patch.explanation,
        "potential_impact": patch.potential_impact,
        "status": patch.status,
        "created_at": patch.created_at.isoformat(),
    }


@router.post("/patches/{patch_id}/approve")
def approve_patch(patch_id: int, db: Session = Depends(get_db)):
    patch = db.query(Patch).filter(Patch.id == patch_id).first()
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")

    patch.status = "approved"
    task = patch.task
    task.status = "approved"

    audit = AuditLog(
        task_id=task.id,
        project_id=task.project_id,
        event_type="PATCH_APPROVED",
        actor="user",
        details_json=json.dumps({"patch_id": patch.id, "target_file": patch.target_file})
    )
    db.add(audit)
    db.commit()

    return {"status": "approved", "patch_id": patch.id}


@router.post("/patches/{patch_id}/reject")
def reject_patch(patch_id: int, db: Session = Depends(get_db)):
    patch = db.query(Patch).filter(Patch.id == patch_id).first()
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")

    patch.status = "rejected"
    task = patch.task
    task.status = "patch_rejected"

    audit = AuditLog(
        task_id=task.id,
        project_id=task.project_id,
        event_type="PATCH_REJECTED",
        actor="user",
        details_json=json.dumps({"patch_id": patch.id, "target_file": patch.target_file})
    )
    db.add(audit)
    db.commit()

    return {"status": "rejected", "patch_id": patch.id}


@router.post("/patches/{patch_id}/rollback")
def rollback_patch(patch_id: int, db: Session = Depends(get_db)):
    patch = db.query(Patch).filter(Patch.id == patch_id).first()
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")

    task = patch.task
    sandbox_path = settings.SANDBOX_DIR / f"task_{task.id}_attempt_{patch.attempt_number}"
    snapshot_path = settings.SANDBOX_DIR / f"task_{task.id}_attempt_{patch.attempt_number}_snapshot"

    restored = restore_rollback_snapshot(snapshot_path, sandbox_path)
    patch.status = "reverted"
    task.status = "reverted"

    audit = AuditLog(
        task_id=task.id,
        project_id=task.project_id,
        event_type="ROLLBACK_PERFORMED",
        actor="user",
        details_json=json.dumps({"patch_id": patch.id, "restored": restored})
    )
    db.add(audit)
    db.commit()

    return {"status": "reverted", "restored": restored}
