import io
import os
import sys
import tempfile
import zipfile
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parents[2]
DATASETS_DIR = ROOT_DIR / "test-datasets"


@pytest.mark.parametrize("zip_name,project_name,expected_test_count", [
    ("bugfix_auth_api.zip", "AuthAPIFix", 4),
    ("bugfix_inventory.zip", "InventoryFix", 4),
    ("bugfix_order_service.zip", "OrderServiceFix", 5),
])
def test_full_autonomous_workflow_on_real_dataset(zip_name, project_name, expected_test_count):
    zip_path = DATASETS_DIR / zip_name
    assert zip_path.exists(), f"Dataset file {zip_path} not found"

    zip_bytes = zip_path.read_bytes()

    # 1. UPLOAD & SCAN
    upload_res = client.post(
        "/api/projects/upload",
        files={"file": (zip_name, zip_bytes, "application/zip")},
        data={"project_name": project_name},
    )
    assert upload_res.status_code == 200, upload_res.text
    upload_data = upload_res.json()
    project_id = upload_data["project"]["id"]

    # 2. DISCOVER BUG_REPORT.md
    bug_report_res = client.get(f"/api/projects/{project_id}/bug-report")
    assert bug_report_res.status_code == 200
    bug_report_data = bug_report_res.json().get("bug_report")
    assert bug_report_data is not None
    assert bug_report_data["has_bug_report"] is True
    assert len(bug_report_data["title"]) > 0

    task_payload = bug_report_data["suggested_task"]

    # 3. CREATE TASK
    task_res = client.post(
        "/api/tasks",
        json={
            "project_id": project_id,
            "bug_title": task_payload["bug_title"],
            "bug_description": task_payload["bug_description"],
            "reproduction_steps": task_payload["reproduction_steps"],
            "expected_behavior": task_payload["expected_behavior"],
            "actual_behavior": task_payload["actual_behavior"],
            "mode": "patch_and_verify"
        }
    )
    assert task_res.status_code == 200
    task_id = task_res.json()["id"]

    # 4. ANALYZE & GENERATE CANDIDATE PATCH
    analyze_res = client.post(f"/api/tasks/{task_id}/analyze")
    assert analyze_res.status_code == 200, analyze_res.text
    analyze_data = analyze_res.json()
    assert analyze_data["patch"] is not None
    patch_id = analyze_data["patch"]["id"]
    assert analyze_data["patch"]["status"] == "proposed"
    assert len(analyze_data["patch"]["diff"]) > 0

    # 5. REVIEW & APPROVE PATCH
    approve_res = client.post(f"/api/patches/{patch_id}/approve")
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # 6. RUN TESTS & REGRESSION GUARDIAN VERIFICATION
    verify_res = client.post(f"/api/tasks/{task_id}/verify")
    assert verify_res.status_code == 200, verify_res.text
    verify_data = verify_res.json()

    assert verify_data["classification"] == "FIX_VERIFIED", f"Expected FIX_VERIFIED, got {verify_data['classification']}: {verify_data.get('guardian_evaluation')}"
    assert verify_data["functional_status"] == "PASSED"
    assert verify_data["regression_status"] == "PASSED"

    post_patch = verify_data["post_patch_tests"]
    assert post_patch["failed_count"] == 0
    assert post_patch["error_count"] == 0
    # Expected unit tests + 1 generated regression test
    assert post_patch["passed_count"] >= expected_test_count

    # 7. DOWNLOAD CORRECTED ZIP
    download_res = client.get(f"/api/projects/{project_id}/download-corrected")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/zip"
    corrected_zip_bytes = download_res.content
    assert len(corrected_zip_bytes) > 0

    # 8. VERIFY DOWNLOADED ZIP INDEPENDENTLY
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(io.BytesIO(corrected_zip_bytes)) as zf:
            zf.extractall(td)

        # Run pytest inside the extracted directory using current environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(td).resolve())
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-v"],
            cwd=td,
            capture_output=True,
            text=True,
            env=env
        )
        assert proc.returncode == 0, f"Pytest failed on extracted corrected zip:\n{proc.stdout}\n{proc.stderr}"
        assert f"{expected_test_count} passed" in proc.stdout or "passed" in proc.stdout
