from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    language: str
    source_type: str
    file_count: int
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]


class FileTreeNode(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None
    children: Optional[List["FileTreeNode"]] = None


class FileContentResponse(BaseModel):
    path: str
    content: str
    size: int
    is_test: bool

