"""Schemas for Docling-based extraction."""

from pydantic import BaseModel


class DoclingPDFToMarkdownResponse(BaseModel):
    """Schema for PDF to Markdown conversion response."""

    project_id: int
    document_id: int
    filename: str
    document_title: str | None
    markdown: str
    page_count: int | None


class DoclingPDFExtractionResponse(BaseModel):
    """Schema for Docling PDF extraction response."""

    project_id: int
    document_title: str | None
    abstract: str | None
    sections_extracted: int
    references_extracted: int
    references_created: int
    references_deduplicated: int
    claims_created: int
