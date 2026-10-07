import io
import json
import shutil
import uuid
import zipfile
import re
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.models.scan import RepositoryScan
from app.models.task import Task
from app.models.audit_log import AuditLog
from app.models.fix_history import FixHistory
from app.models.patch import Patch
from app.models.test_run import TestRun
from app.models.verification import VerificationReport
from app.security.archive_validator import validate_and_extract_archive
from app.security.path_validator import validate_safe_path
from app.services.repository_scanner import scan_repository, detect_repo_language, parse_bug_report
from app.services.demo_service import create_demo_zip, DEMO_PROJECT_NAME

import logging

logger = logging.getLogger("codepilot.projects")
router = APIRouter()


@router.post("/projects/upload")
async def upload_project(
    file: UploadFile = File(...),
    project_name: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    final_name = (project_name or name or "").strip()
    if not final_name:
        raise HTTPException(status_code=422, detail="Project name is required ('name' or 'project_name')")

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP archives are supported")

    content = await file.read()

    # Safety first: Extract to a temporary isolated folder to validate
    temp_dir_name = f"staging_{uuid.uuid4().hex}"
    temp_dest = settings.STORAGE_DIR / "staging" / temp_dir_name

    try:
        extracted = validate_and_extract_archive(content, temp_dest)

        # Verify the archive contains Python files
        scan_results = scan_repository(temp_dest)
        if scan_results["python_files"] == 0:
            detected_lang = detect_repo_language(temp_dest)
            shutil.rmtree(temp_dest, ignore_errors=True)
            raise HTTPException(
                status_code=400,
                detail=f"ZIP uploaded successfully, but no Python files were found. This scanner currently supports Python repositories (detected: {detected_lang})."
            )

        # Create project record in database
        project_record = Project(
            name=final_name,
            language="python",
            source_type="upload",
            storage_path="",
            file_count=len(extracted)
        )
        db.add(project_record)
        db.commit()
        db.refresh(project_record)

        # Move from staging to permanent project storage
        dest_dir = settings.PROJECTS_DIR / f"project_{project_record.id}"
        if dest_dir.exists():
            shutil.rmtree(dest_dir, ignore_errors=True)
        shutil.move(str(temp_dest), str(dest_dir))

        # Update project storage path
        project_record.storage_path = str(dest_dir.resolve())
        db.commit()

        # Perform AST repository scan in permanent location
        perm_scan_results = scan_repository(dest_dir, final_name)
        scan_record = RepositoryScan(
            project_id=project_record.id,
            total_files=perm_scan_results["total_files"],
            python_files=perm_scan_results["python_files"],
            test_files=perm_scan_results["test_files"],
            syntax_errors_count=perm_scan_results["syntax_errors_count"],
            dependencies_json=json.dumps(perm_scan_results["dependencies"]),
            manifest_json=json.dumps(perm_scan_results.get("manifest", {})),
            inventory_json=json.dumps(perm_scan_results.get("inventory", [])),
            dependency_graph_json=json.dumps(perm_scan_results.get("dependency_graph", {})),
            file_tree_json=json.dumps(perm_scan_results["file_tree"]),
            symbols_json=json.dumps(perm_scan_results["symbols"])
        )
        db.add(scan_record)

        # Log real agent discovery and indexing audit events
        db.add(AuditLog(
            project_id=project_record.id,
            event_type="REPOSITORY_UPLOADED",
            actor="user",
            details_json=json.dumps({"filename": file.filename, "size_bytes": len(content)})
        ))
        db.add(AuditLog(
            project_id=project_record.id,
            event_type="EXTRACTING_REPOSITORY",
            actor="system",
            details_json=json.dumps({"extracted_files": len(extracted), "workspace": str(dest_dir)})
        ))
        db.add(AuditLog(
            project_id=project_record.id,
            event_type="REPOSITORY_DISCOVERED",
            actor="agent",
            details_json=json.dumps({
                "total_files": perm_scan_results["total_files"],
                "source_files": perm_scan_results.get("manifest", {}).get("source_files", perm_scan_results["python_files"]),
                "test_files": perm_scan_results["test_files"],
                "config_files": perm_scan_results.get("manifest", {}).get("config_files", 0)
            })
        ))
        db.add(AuditLog(
            project_id=project_record.id,
            event_type="REPOSITORY_INDEXED",
            actor="agent",
            details_json=json.dumps({
                "python_files": perm_scan_results["python_files"],
                "symbols_indexed": len(perm_scan_results["symbols"])
            })
        ))
        db.add(AuditLog(
            project_id=project_record.id,
            event_type="TESTS_DISCOVERED",
            actor="agent",
            details_json=json.dumps({
                "test_framework": perm_scan_results.get("manifest", {}).get("test_framework", "pytest"),
                "test_files": perm_scan_results["test_files"]
            })
        ))
        db.add(AuditLog(
            project_id=project_record.id,
            event_type="DEPENDENCY_GRAPH_BUILT",
            actor="agent",
            details_json=json.dumps({
                "nodes": len(perm_scan_results.get("dependency_graph", {}).get("nodes", [])),
                "edges": len(perm_scan_results.get("dependency_graph", {}).get("edges", []))
            })
        ))
        db.commit()
        db.refresh(project_record)

        return {
            "project": {
                "id": project_record.id,
                "name": project_record.name,
                "language": project_record.language,
                "file_count": project_record.file_count,
                "created_at": project_record.created_at.isoformat()
            },
            "scan": {
                "python_files": perm_scan_results["python_files"],
                "test_files": perm_scan_results["test_files"],
                "syntax_errors": perm_scan_results["syntax_errors_count"]
            }
        }
    except HTTPException:
        if temp_dest.exists():
            shutil.rmtree(temp_dest, ignore_errors=True)
        raise
    except Exception as e:
        if temp_dest.exists():
            shutil.rmtree(temp_dest, ignore_errors=True)
        logger.exception("[PROJECT] Project upload unexpected error: %s", str(e))
        raise HTTPException(status_code=500, detail="Repository upload failed due to server error.")


@router.post("/projects/demo/load")
def load_demo_project(db: Session = Depends(get_db)):
    """Loads the pre-packaged demo project with deliberate boundary bug."""
    logger.info("[PROJECT] Demo creation started")
    demo_zip_bytes = create_demo_zip()

    project_record = Project(
        name=DEMO_PROJECT_NAME,
        description="Demo e-commerce pricing engine with off-by-one boundary bug in tier discount calculation.",
        language="python",
        source_type="demo",
        storage_path="",
        file_count=0
    )
    db.add(project_record)
    db.commit()
    db.refresh(project_record)

    dest_dir = settings.PROJECTS_DIR / f"project_{project_record.id}"
    extracted = validate_and_extract_archive(demo_zip_bytes, dest_dir)
    logger.info(f"[PROJECT] Demo workspace created at {dest_dir} ({len(extracted)} files)")

    project_record.storage_path = str(dest_dir.resolve())
    project_record.file_count = len(extracted)

    scan_results = scan_repository(dest_dir, DEMO_PROJECT_NAME)
    logger.info(f"[SCAN] Python files: {scan_results['python_files']}, Test files: {scan_results['test_files']}")

    scan_record = RepositoryScan(
        project_id=project_record.id,
        total_files=scan_results["total_files"],
        python_files=scan_results["python_files"],
        test_files=scan_results["test_files"],
        syntax_errors_count=scan_results["syntax_errors_count"],
        dependencies_json=json.dumps(scan_results["dependencies"]),
        manifest_json=json.dumps(scan_results.get("manifest", {})),
        inventory_json=json.dumps(scan_results.get("inventory", [])),
        dependency_graph_json=json.dumps(scan_results.get("dependency_graph", {})),
        file_tree_json=json.dumps(scan_results["file_tree"]),
        symbols_json=json.dumps(scan_results["symbols"])
    )
    db.add(scan_record)

    audit = AuditLog(
        project_id=project_record.id,
        event_type="DEMO_LOADED",
        actor="system",
        details_json=json.dumps({"demo_name": DEMO_PROJECT_NAME})
    )
    db.add(audit)
    db.commit()
    db.refresh(project_record)
    logger.info(f"[PROJECT] Demo project saved: ID {project_record.id}")

    return {
        "project": {
            "id": project_record.id,
            "name": project_record.name,
            "language": project_record.language,
            "file_count": project_record.file_count,
            "source_type": "demo",
            "created_at": project_record.created_at.isoformat()
        },
        "scan": scan_results
    }


@router.post("/projects/demo/reset")
def reset_demo_project(db: Session = Depends(get_db)):
    """Resets the built-in ShopPilot demo project to its original buggy state."""
    logger.info("[PROJECT] Demo project reset requested")

    # 1. Locate any existing demo projects
    existing_demos = db.query(Project).filter(
        (Project.source_type == "demo") | (Project.name == DEMO_PROJECT_NAME)
    ).all()

    for demo_p in existing_demos:
        # Clean up any fix history for demo project
        db.query(FixHistory).filter(FixHistory.project_id == demo_p.id).delete()

        # Remove directories
        storage_dir = Path(demo_p.storage_path) if demo_p.storage_path else settings.PROJECTS_DIR / f"project_{demo_p.id}"
        if storage_dir.exists():
            shutil.rmtree(storage_dir, ignore_errors=True)
        corrected_dir = settings.PROJECTS_DIR / f"project_{demo_p.id}_corrected"
        if corrected_dir.exists():
            shutil.rmtree(corrected_dir, ignore_errors=True)

        # Delete database record (cascades to tasks, patches, test runs, scans, audit logs)
        db.delete(demo_p)

    db.commit()

    # 2. Re-create clean demo project
    demo_zip_bytes = create_demo_zip()

    project_record = Project(
        name=DEMO_PROJECT_NAME,
        description="Demo e-commerce pricing engine with off-by-one boundary bug in tier discount calculation.",
        language="python",
        source_type="demo",
        storage_path="",
        file_count=0
    )
    db.add(project_record)
    db.commit()
    db.refresh(project_record)

    dest_dir = settings.PROJECTS_DIR / f"project_{project_record.id}"
    extracted = validate_and_extract_archive(demo_zip_bytes, dest_dir)

    project_record.storage_path = str(dest_dir.resolve())
    project_record.file_count = len(extracted)

    scan_results = scan_repository(dest_dir, DEMO_PROJECT_NAME)
    scan_record = RepositoryScan(
        project_id=project_record.id,
        total_files=scan_results["total_files"],
        python_files=scan_results["python_files"],
        test_files=scan_results["test_files"],
        syntax_errors_count=scan_results["syntax_errors_count"],
        dependencies_json=json.dumps(scan_results["dependencies"]),
        manifest_json=json.dumps(scan_results.get("manifest", {})),
        inventory_json=json.dumps(scan_results.get("inventory", [])),
        dependency_graph_json=json.dumps(scan_results.get("dependency_graph", {})),
        file_tree_json=json.dumps(scan_results["file_tree"]),
        symbols_json=json.dumps(scan_results["symbols"])
    )
    db.add(scan_record)

    audit = AuditLog(
        project_id=project_record.id,
        event_type="DEMO_RESET",
        actor="user",
        details_json=json.dumps({"demo_name": DEMO_PROJECT_NAME})
    )
    db.add(audit)
    db.commit()
    db.refresh(project_record)
    logger.info(f"[PROJECT] Demo project reset complete: New ID {project_record.id}")

    return {
        "status": "ok",
        "message": "ShopPilot demo project reset to original buggy state for clean evaluation.",
        "project": {
            "id": project_record.id,
            "name": project_record.name,
            "language": project_record.language,
            "file_count": project_record.file_count,
            "source_type": "demo",
            "created_at": project_record.created_at.isoformat()
        },
        "scan": scan_results
    }


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    results = []
    for p in projects:
        results.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "language": p.language,
            "source_type": p.source_type,
            "file_count": p.file_count,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat() if p.updated_at else p.created_at.isoformat(),
        })
    return {"projects": results}


@router.get("/projects/{project_id}")
def get_project_details(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo_dir = Path(project.storage_path) if project.storage_path else None
    bug_report = parse_bug_report(repo_dir) if (repo_dir and repo_dir.exists()) else None
    has_verified_fix = db.query(Task).filter(Task.project_id == project_id, Task.status == "verified").first() is not None

    scan_info = None
    if project.scan:
        scan_info = {
            "total_files": project.scan.total_files,
            "python_files": project.scan.python_files,
            "test_files": project.scan.test_files,
            "syntax_errors_count": project.scan.syntax_errors_count,
            "dependencies": json.loads(project.scan.dependencies_json or "[]"),
            "manifest": json.loads(project.scan.manifest_json or "{}"),
            "inventory": json.loads(project.scan.inventory_json or "[]"),
            "dependency_graph": json.loads(project.scan.dependency_graph_json or "{}"),
            "symbols": json.loads(project.scan.symbols_json or "{}"),
            "bug_report": bug_report
        }

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "language": project.language,
            "source_type": project.source_type,
            "file_count": project.file_count,
            "has_verified_fix": has_verified_fix,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat() if project.updated_at else project.created_at.isoformat(),
        },
        "scan": scan_info,
        "bug_report": bug_report
    }


@router.get("/projects/{project_id}/tree")
def get_project_tree(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.scan and project.scan.file_tree_json:
        return {"tree": json.loads(project.scan.file_tree_json)}

    repo_dir = Path(project.storage_path)
    if not repo_dir.exists():
        return {"tree": []}
    scan_res = scan_repository(repo_dir)
    return {"tree": scan_res["file_tree"]}


@router.get("/projects/{project_id}/files")
def get_file_content(
    project_id: int,
    path: str = Query(..., description="Relative file path"),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo_dir = Path(project.storage_path)
    file_path = validate_safe_path(path, repo_dir)

    if not file_path.exists() or file_path.is_dir():
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    content = file_path.read_text(encoding="utf-8", errors="replace")
    is_test = "test" in path.lower()

    return {
        "path": path,
        "content": content,
        "size": file_path.stat().st_size,
        "is_test": is_test
    }


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    storage_dir = Path(project.storage_path)
    if storage_dir.exists():
        shutil.rmtree(storage_dir, ignore_errors=True)

    corrected_dir = settings.PROJECTS_DIR / f"project_{project.id}_corrected"
    if corrected_dir.exists():
        shutil.rmtree(corrected_dir, ignore_errors=True)

    db.delete(project)
    db.commit()
    return {"status": "deleted", "project_id": project_id}


@router.get("/projects/{project_id}/bug-report")
def get_bug_report(project_id: int, db: Session = Depends(get_db)):
    """Fetches detected BUG_REPORT.md information for the project repository."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo_dir = Path(project.storage_path) if project.storage_path else None
    if not repo_dir or not repo_dir.exists():
        return {"bug_report": None}

    return {"bug_report": parse_bug_report(repo_dir)}


@router.get("/projects/{project_id}/corrected-zip")
@router.get("/projects/{project_id}/download-corrected")
def download_corrected_repository(project_id: int, db: Session = Depends(get_db)):
    """Downloads the verified corrected codebase as a clean ZIP archive with 6 strict precondition checks."""
    # Precondition 1: Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Precondition 2: Verify task is verified
    verified_task = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "verified"
    ).order_by(Task.updated_at.desc()).first()
    if not verified_task:
        raise HTTPException(
            status_code=400,
            detail="Cannot download corrected repository: No verified bug fix exists for this project yet. Complete the investigation, review the patch, and verify with Regression Guardian first."
        )

    # Precondition 3: Verify patch is applied
    applied_patch = db.query(Patch).filter(
        Patch.task_id == verified_task.id,
        Patch.status.in_(["applied", "approved"])
    ).first()
    if not applied_patch and not verified_task.patches:
        raise HTTPException(
            status_code=400,
            detail="Cannot download: No applied patch exists for this verified task."
        )

    # Precondition 4: Verify test runs completed
    test_runs = db.query(TestRun).filter(TestRun.task_id == verified_task.id).all()
    has_baseline = any(tr.stage == "baseline" for tr in test_runs)
    has_post_patch = any(tr.stage == "post_patch" for tr in test_runs)
    if not (has_baseline and has_post_patch):
        raise HTTPException(
            status_code=400,
            detail="Cannot download: Test suite execution has not completed for both baseline and post-patch stages."
        )

    # Precondition 5: Verify verification passed
    report = db.query(VerificationReport).filter(VerificationReport.task_id == verified_task.id).first()
    if not report or report.classification != "FIX_VERIFIED" or report.functional_status != "PASSED":
        raise HTTPException(
            status_code=400,
            detail="Cannot download: Verification has not passed or was not marked as FIX_VERIFIED."
        )

    # Precondition 6: Verify regressions == 0
    if report.regression_status != "PASSED":
        raise HTTPException(
            status_code=400,
            detail="Cannot download: Regressions were detected in the test suite."
        )
    evidence = {}
    try:
        evidence = json.loads(report.evidence_summary_json or "{}")
    except Exception:
        pass
    regressed_tests = evidence.get("regressed_tests", [])
    if len(regressed_tests) > 0 or evidence.get("regressions_count", 0) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot download: Regressions detected ({len(regressed_tests)} tests regressed)."
        )

    repo_dir = Path(project.storage_path) if project.storage_path else None
    if not repo_dir or not repo_dir.exists():
        raise HTTPException(status_code=404, detail="Original project repository directory not found.")

    corrected_dir = Path(project.corrected_storage_path) if project.corrected_storage_path else (settings.PROJECTS_DIR / f"project_{project.id}_corrected")

    # Materialize on the fly if needed
    if not corrected_dir.exists():
        shutil.copytree(
            repo_dir,
            corrected_dir,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".venv", "storage", "*.pyc")
        )
        if verified_task.patches:
            lp = sorted(verified_task.patches, key=lambda x: x.attempt_number, reverse=True)[0]
            target = (corrected_dir / lp.target_file).resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(lp.new_code, encoding="utf-8")
        project.corrected_storage_path = str(corrected_dir.resolve())
        db.commit()

    # Build clean in-memory ZIP archive
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(corrected_dir.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(corrected_dir)
                parts = rel_path.parts
                # Strictly exclude internal / temporary files per spec:
                # .git/, .env*, .venv/, node_modules/, __pycache__/, *.pyc, test_codepilot_regression.py
                if any(p in {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "storage"} for p in parts):
                    continue
                if any(p.startswith(".env") for p in parts):
                    continue
                if file_path.name.endswith(".pyc") or file_path.name == "test_codepilot_regression.py":
                    continue
                zf.write(file_path, str(rel_path).replace("\\", "/"))

    buf.seek(0)
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", project.name).strip("_") or f"project_{project.id}"
    filename = f"{safe_name}_corrected.zip"

    audit = AuditLog(
        project_id=project.id,
        task_id=verified_task.id,
        event_type="CORRECTED_ZIP_DOWNLOADED",
        actor="user",
        details_json=json.dumps({"filename": filename, "endpoint": "corrected-zip"})
    )
    db.add(audit)
    db.commit()

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

