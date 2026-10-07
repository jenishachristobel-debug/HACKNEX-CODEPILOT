from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class TestDetail(BaseModel):
    name: str
    status: str  # PASSED, FAILED, SKIPPED, ERROR
    duration_ms: Optional[int] = 0
    message: Optional[str] = None


class TestRunResponse(BaseModel):
    id: int
    task_id: int
    attempt_number: int
    stage: str  # baseline, post_patch, regression_generated
    command: str
    exit_code: int
    duration_ms: int
    passed_count: int
    failed_count: int
    error_count: int
    output_log: str
    test_details: List[TestDetail]
    created_at: datetime

    class Config:
        from_attributes = True


class VerificationResponse(BaseModel):
    id: int
    task_id: int
    classification: str
    functional_status: str
    regression_status: str
    syntax_status: str
    security_status: str
    evidence_summary: Dict[str, Any]
    markdown_report: str
    json_report: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

