from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[Literal['draft', 'processing', 'ready']] = 'draft'


class ProjectCreate(ProjectBase):
    name: str


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal['draft', 'processing', 'ready']] = None
    document_path: Optional[str] = None
    document_filename: Optional[str] = None


class ProjectOut(ProjectBase):
    id: int
    document_path: Optional[str] = None
    document_filename: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

