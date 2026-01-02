"""API endpoints for document management."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.document import Document
from app.schemas.document import DocumentOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve a document by ID.

    Args:
        document_id: Document ID
        session: Database session

    Returns:
        Document with markdown content
    """
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.get("/project/{project_id}", response_model=List[DocumentOut])
async def get_project_documents(
    project_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve all documents for a project.

    Args:
        project_id: Project ID
        session: Database session

    Returns:
        List of documents for the project
    """
    result = await session.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return list(documents)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Delete a document by ID.

    Args:
        document_id: Document ID
        session: Database session

    Returns:
        Success message
    """
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    await session.delete(document)
    await session.commit()

    return {"message": "Document deleted successfully", "id": document_id}
