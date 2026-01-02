from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    filename: str
    document_title: Optional[str] = None
    markdown_content: str
    page_count: Optional[int] = None


class DocumentCreate(DocumentBase):
    project_id: int


class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    document_title: Optional[str] = None
    markdown_content: Optional[str] = None
    page_count: Optional[int] = None


class DocumentOut(DocumentBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
