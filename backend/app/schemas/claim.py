from datetime import datetime

from pydantic import BaseModel


class ClaimBase(BaseModel):
    """Base schema for Claim"""

    text: str
    claim_type: str | None = None
    page_number: int | None = None
    paragraph_index: int | None = None


class ClaimCreate(ClaimBase):
    """Schema for creating a claim"""

    project_id: int
    reference_ids: list[int] = []  # Optional list of reference IDs to link


class ClaimUpdate(BaseModel):
    """Schema for updating a claim"""

    text: str | None = None
    claim_type: str | None = None
    page_number: int | None = None
    paragraph_index: int | None = None
    verification_status: str | None = None


class ClaimReferenceOut(BaseModel):
    """Schema for claim-reference link output"""

    reference_id: int
    relevance_score: float | None = None
    context: str | None = None

    class Config:
        from_attributes = True


class ClaimOut(ClaimBase):
    """Schema for claim output"""

    id: int
    project_id: int
    verification_status: str
    created_at: datetime
    updated_at: datetime
    references: list[int] = []  # List of reference IDs

    class Config:
        from_attributes = True


class ClaimWithReferences(ClaimOut):
    """Schema for claim with full reference details"""

    reference_details: list["ReferenceOut"] = []

    class Config:
        from_attributes = True


# Import for type hints
from app.schemas.reference import ReferenceOut  # noqa: E402

ClaimWithReferences.model_rebuild()
