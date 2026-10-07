import io
import sys
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app
from app.services.regression_guardian import classify_regression

client = TestClient(app)


def test_demo_project_flow_and_regression_guardian():
    # 1. Load Demo Project
    demo_resp = client.post("/api/projects/demo/load")
    assert demo_resp.status_code == 200, demo_resp.text
    project_id = demo_resp.json()["project"]["id"]

    # 2. Check File Tree & File Content
    tree_resp = client.get(f"/api/projects/{project_id}/tree")
    assert tree_resp.status_code == 200
    assert len(tree_resp.json()["tree"]) > 0

    file_resp = client.get(f"/api/projects/{project_id}/files?path=calculator.py")
    assert file_resp.status_code == 200
    assert "calculate_discount" in file_resp.json()["content"]

    # 3. Create Task
    task_resp = client.post("/api/tasks", json={
        "project_id": project_id,
        "bug_title": "Orders of exactly $100 fail to receive Tier-1 discount",
        "bug_description": "Boundary check total > 100 excludes the $100.00 threshold.",
        "expected_behavior": "calculate_discount(100.0) returns 10.0",
        "mode": "patch_and_verify"
    })
    assert task_resp.status_code == 200
    task_id = task_resp.json()["id"]

    # 4. Trigger Analysis
    analysis_resp = client.post(f"/api/tasks/{task_id}/analyze")
    assert analysis_resp.status_code == 200
    analysis_data = analysis_resp.json()
    assert "analysis" in analysis_data
    assert "patch" in analysis_data
    assert analysis_data["patch"]["target_file"] == "calculator.py"
    patch_id = analysis_data["patch"]["id"]

    # 5. Approve Patch
    approve_resp = client.post(f"/api/patches/{patch_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # 6. Run Verification via Regression Guardian
    verify_resp = client.post(f"/api/tasks/{task_id}/verify")
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["classification"] in ("FIX_VERIFIED", "PARTIALLY_VERIFIED")
    assert verify_data["syntax_status"] == "PASSED"
    assert verify_data["security_status"] == "PASSED"

    # 7. Check Verification Report & Export
    report_id = verify_data["report_id"]
    rep_resp = client.get(f"/api/reports/{report_id}")
    assert rep_resp.status_code == 200
    assert "markdown_report" in rep_resp.json()

    export_resp = client.get(f"/api/reports/{report_id}/export?format=markdown")
    assert export_resp.status_code == 200
    assert "Evidence-Based Verification Report" in export_resp.text

    # 8. Check Fix History
    history_resp = client.get("/api/history")
    assert history_resp.status_code == 200
    assert len(history_resp.json()["history"]) > 0


def test_regression_guardian_classifies_regressions():
    # Simulate baseline run where 2 tests pass
    baseline_run = {
        "exit_code": 0,
        "passed_count": 2,
        "failed_count": 0,
        "test_details": [
            {"name": "test_shipping", "status": "PASSED"},
            {"name": "test_discount_zero", "status": "PASSED"},
        ]
    }

    # Simulate post-patch run where test_shipping broke!
    post_patch_run = {
        "exit_code": 1,
        "passed_count": 1,
        "failed_count": 1,
        "test_details": [
            {"name": "test_shipping", "status": "FAILED"},
            {"name": "test_discount_zero", "status": "PASSED"},
        ]
    }

    result = classify_regression(baseline_run, post_patch_run)
    assert result["classification"] == "REGRESSION_DETECTED"
    assert "test_shipping" in result["regressed_tests"]
    assert "Regression detected" in result["explanation"]

