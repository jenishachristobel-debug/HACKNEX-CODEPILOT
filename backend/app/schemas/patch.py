from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class PatchContent(BaseModel):
    target_file: str
    new_code: str
    original_code: Optional[str] = None
    explanation: Optional[str] = None


class PatchValidateRequest(BaseModel):
    project_id: int
    patch: PatchContent


class PatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    attempt_number: int
    target_file: str
    original_code: str
    new_code: str
    diff: str
    explanation: Optional[str] = None
    potential_impact: Optional[str] = None
    status: str
    created_at: datetime


class PatchListResponse(BaseModel):
    patches: List[PatchResponse]

