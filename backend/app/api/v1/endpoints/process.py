"""API endpoints for document and text processing."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.claim import Claim
from app.models.claim_reference import ClaimReference
from app.models.document import Document
from app.models.project import Project
from app.models.reference import Reference
from app.schemas.docling_extraction import DoclingPDFToMarkdownResponse
from app.schemas.extraction import TextExtractionRequest, TextExtractionResponse
from app.services.docling_service import get_docling_service
from app.services.lm_studio_client import get_lm_studio_client, LMStudioError
from app.services.reference_dedup import compute_dedup_hash
from app.services.text_extraction import (
    extract_claims_and_references,
    validate_reference_indices,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/process", tags=["process"])


@router.post("/pdf", response_model=DoclingPDFToMarkdownResponse)
async def process_pdf(
    project_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    """
    Process PDF document and extract markdown.

    This endpoint:
    1. Converts PDF to clean Markdown format using Docling
    2. Stores the markdown in the database for later RAG processing
    3. Returns the markdown for viewing and manual reference selection

    Args:
        project_id: Project ID to associate the document with
        file: PDF file upload
        session: Database session

    Returns:
        Document ID and markdown content
    """
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify file is PDF (only check filename extension, ignore MIME type for cloud storage compatibility)
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Invalid file upload attempt: filename={file.filename}, content_type={file.content_type}")
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
        )

    logger.info(f"Processing PDF: {file.filename}, content_type={file.content_type}")

    # Read PDF content
    pdf_content = await file.read()

    # Get Docling service
    docling = get_docling_service()

    # Process PDF with Docling
    try:
        parsed_data = docling.process_pdf(pdf_content, filename=file.filename or "document.pdf")
    except Exception as e:
        logger.error(f"Docling PDF processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF with Docling: {str(e)}"
        ) from e

    # Update project with document info
    project.document_filename = file.filename

    # Create document record
    document = Document(
        project_id=project_id,
        filename=file.filename or "document.pdf",
        document_title=parsed_data.get("title"),
        markdown_content=parsed_data.get("markdown", ""),
        page_count=parsed_data.get("metadata", {}).get("page_count"),
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    return DoclingPDFToMarkdownResponse(
        project_id=project_id,
        document_id=document.id,
        filename=file.filename or "document.pdf",
        document_title=parsed_data.get("title"),
        markdown=parsed_data.get("markdown", ""),
        page_count=parsed_data.get("metadata", {}).get("page_count"),
    )


@router.post("/text", response_model=TextExtractionResponse)
async def process_text(
    request: TextExtractionRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Extract claims and references from text using LM Studio.

    This endpoint:
    1. Uses LLM to extract claims and references from the provided text
    2. Deduplicates references against existing database entries
    3. Creates new claims linked to the project
    4. Links claims to their supporting references

    Args:
        request: Text extraction request with text and project_id
        session: Database session

    Returns:
        Extraction response with statistics
    """
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == request.project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get LM Studio client
    try:
        lm_client = get_lm_studio_client()
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail="LM Studio service not available. Please ensure LM Studio is running."
        ) from e

    # Extract claims and references using LLM
    try:
        extraction_result = await extract_claims_and_references(
            lm_client,
            request.text
        )
        extraction_result = validate_reference_indices(extraction_result)
    except LMStudioError as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract claims and references: {str(e)}"
        ) from e

    # Process references with deduplication
    reference_map = {}  # Maps extraction index to database reference ID
    references_created = 0
    references_deduplicated = 0

    for idx, extracted_ref in enumerate(extraction_result.references):
        # Compute dedup hash
        dedup_hash = compute_dedup_hash(
            title=extracted_ref.title,
            authors=extracted_ref.authors,
            doi=extracted_ref.doi
        )

        # Check if reference already exists
        result = await session.execute(
            select(Reference).where(Reference.dedup_hash == dedup_hash)
        )
        existing_ref = result.scalar_one_or_none()

        if existing_ref:
            # Use existing reference
            reference_map[idx] = existing_ref.id
            references_deduplicated += 1
            logger.info(f"Found existing reference: {existing_ref.title}")
        else:
            # Create new reference
            new_ref = Reference(
                title=extracted_ref.title,
                authors=extracted_ref.authors,
                year=extracted_ref.year,
                source=extracted_ref.source,
                doi=extracted_ref.doi,
                url=extracted_ref.url,
                dedup_hash=dedup_hash,
            )
            session.add(new_ref)
            await session.flush()  # Get the ID
            reference_map[idx] = new_ref.id
            references_created += 1
            logger.info(f"Created new reference: {new_ref.title}")

    # Process claims
    claims_created = 0

    for extracted_claim in extraction_result.claims:
        # Create claim
        new_claim = Claim(
            project_id=request.project_id,
            text=extracted_claim.text,
            claim_type=extracted_claim.claim_type,
            page_number=extracted_claim.page_number,
            paragraph_index=extracted_claim.paragraph_index,
            verification_status="unverified"
        )
        session.add(new_claim)
        await session.flush()  # Get the ID

        # Link claim to references
        for ref_idx in extracted_claim.reference_indices:
            if ref_idx in reference_map:
                claim_ref = ClaimReference(
                    claim_id=new_claim.id,
                    reference_id=reference_map[ref_idx]
                )
                session.add(claim_ref)

        claims_created += 1
        logger.info(
            f"Created claim with {len(extracted_claim.reference_indices)} references: "
            f"{extracted_claim.text[:50]}..."
        )

    # Commit all changes
    await session.commit()

    return TextExtractionResponse(
        project_id=request.project_id,
        extraction_result=extraction_result,
        claims_created=claims_created,
        references_created=references_created,
        references_deduplicated=references_deduplicated
    )
