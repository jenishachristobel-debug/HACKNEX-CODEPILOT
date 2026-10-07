from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RootCauseStructure(BaseModel):
    summary: str
    root_cause: str
    affected_files: List[str] = Field(default_factory=list)
    affected_functions: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    proposed_plan: List[str] = Field(default_factory=list)
    potential_side_effects: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    call_path: str = ""
    expected_behavior: str = ""
    actual_behavior: str = ""
    proposed_fix: str = ""


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    summary: str
    root_cause: str
    affected_files: List[str]
    affected_functions: List[str]
    call_path: str = ""
    evidence: List[str]
    proposed_plan: List[str]
    potential_side_effects: List[str]
    uncertainties: List[str]
    expected_behavior: str = ""
    actual_behavior: str = ""
    proposed_fix: str = ""
    is_llm_generated: bool
    created_at: datetime

