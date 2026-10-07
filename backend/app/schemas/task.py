from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    project_id: int
    bug_title: str
    bug_description: str
    error_traceback: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    reproduction_steps: Optional[str] = None
    mode: Optional[str] = "patch_and_verify"


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    bug_title: str
    bug_description: str
    error_traceback: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    reproduction_steps: Optional[str] = None
    mode: str
    status: str
    current_attempt: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]

