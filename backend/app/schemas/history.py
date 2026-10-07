from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class FixHistoryItem(BaseModel):
    id: int
    project_id: Optional[int] = None
    project_name: str
    bug_title: str
    root_cause_summary: Optional[str] = None
    target_file: Optional[str] = None
    patch_summary: Optional[str] = None
    outcome: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    history: List[FixHistoryItem]

