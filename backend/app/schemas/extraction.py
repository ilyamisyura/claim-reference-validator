"""Schemas for text extraction."""

from pydantic import BaseModel, Field


class ExtractedReference(BaseModel):
    """Schema for an extracted reference from text."""

    title: str = Field(..., description="Title of the reference")
    authors: str = Field(..., description="Authors of the reference (comma-separated or formatted)")
    year: int | None = Field(None, description="Publication year")
    source: str | None = Field(None, description="Source (journal, conference, book, etc.)")
    doi: str | None = Field(None, description="DOI if available")
    url: str | None = Field(None, description="URL if available")


class ExtractedClaim(BaseModel):
    """Schema for an extracted claim from text."""

    text: str = Field(..., description="The claim text")
    claim_type: str | None = Field(None, description="Type of claim (factual, statistical, opinion, etc.)")
    page_number: int | None = Field(None, description="Page number where claim appears")
    paragraph_index: int | None = Field(None, description="Paragraph index")
    reference_indices: list[int] = Field(
        default_factory=list,
        description="Indices of references that support this claim (0-based index into the references list)"
    )


class ExtractionResult(BaseModel):
    """Schema for the complete extraction result."""

    claims: list[ExtractedClaim] = Field(default_factory=list, description="Extracted claims")
    references: list[ExtractedReference] = Field(default_factory=list, description="Extracted references")


class TextExtractionRequest(BaseModel):
    """Schema for text extraction request."""

    text: str = Field(..., description="Text to extract claims and references from")
    project_id: int = Field(..., description="Project ID to associate the extracted claims with")


class TextExtractionResponse(BaseModel):
    """Schema for text extraction response."""

    project_id: int
    extraction_result: ExtractionResult
    claims_created: int
    references_created: int
    references_deduplicated: int
