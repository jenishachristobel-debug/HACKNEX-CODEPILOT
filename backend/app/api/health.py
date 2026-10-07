import sys
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database import get_db
from app.services.ai_provider import ai_provider_service

router = APIRouter()


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    test_runner_status = "ready"
    try:
        import pytest  # noqa: F401
        if not Path(sys.executable).exists():
            test_runner_status = "error: python runtime missing"
    except Exception as e:
        test_runner_status = f"error: {str(e)}"

    scanner_status = "ready"
    try:
        if not settings.PROJECTS_DIR.exists():
            settings.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        scanner_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "backend": "healthy",
        "database": db_status,
        "test_runner": test_runner_status,
        "repository_scanner": scanner_status,
        "version": settings.VERSION,
        "execution_mode": settings.EXECUTION_MODE,
        "ai_provider": ai_provider_service.get_status(),
    }


@router.get("/health/ai")
def get_ai_health():
    return ai_provider_service.get_status()


@router.get("/settings/status")
def get_settings_status():
    configured = ai_provider_service.is_configured()
    return {
        "execution_engine": "safe_subprocess" if settings.EXECUTION_MODE != "docker" else "docker",
        "reasoning_engine": "live_llm" if configured else "offline_ast",
        "max_repair_attempts": settings.MAX_REPAIR_ATTEMPTS,
        "subprocess_timeout": settings.TEST_TIMEOUT_SECONDS,
        "max_upload_mb": settings.MAX_ARCHIVE_SIZE_BYTES // (1024 * 1024),
        "human_approval_required": True,
        "self_repair_in_sandbox": True,
        "baseline_tests_enabled": True,
        "regression_tests_enabled": True,
        "post_patch_tests_enabled": True,
        "stop_on_regression": True,
        "archive_validation": True,
        "path_traversal_protection": True,
        "symlink_protection": True,
        "secret_redaction": True,
        "unsafe_command_blocking": True
    }

