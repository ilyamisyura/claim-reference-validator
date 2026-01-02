from datetime import datetime

from pydantic import BaseModel, Field


class ReferenceBase(BaseModel):
    """Base schema for Reference"""

    doi: str | None = None
    title: str
    authors: str
    source: str | None = None
    year: int | None = None
    url: str | None = None


class ReferenceCreate(ReferenceBase):
    """Schema for creating a reference"""

    pass


class ReferenceUpdate(BaseModel):
    """Schema for updating a reference"""

    doi: str | None = None
    title: str | None = None
    authors: str | None = None
    source: str | None = None
    year: int | None = None
    url: str | None = None
    is_processed: bool | None = None


class ReferenceOut(ReferenceBase):
    """Schema for reference output"""

    id: int
    dedup_hash: str
    is_processed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
