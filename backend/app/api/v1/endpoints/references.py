from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.reference import Reference
from app.schemas.pagination import PaginatedResponse
from app.schemas.reference import ReferenceCreate, ReferenceOut, ReferenceUpdate
from app.services.reference_dedup import compute_dedup_hash, should_merge_references


router = APIRouter(prefix="/references", tags=["references"])


@router.get("/", response_model=PaginatedResponse[ReferenceOut])
async def list_references(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """List all references with pagination."""
    # Get total count
    count_result = await db.execute(select(func.count()).select_from(Reference))
    total = count_result.scalar_one()

    # Calculate offset
    offset = (page - 1) * page_size

    # Get paginated results
    result = await db.execute(
        select(Reference)
        .order_by(Reference.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=ReferenceOut, status_code=status.HTTP_201_CREATED)
async def create_reference(
    payload: ReferenceCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create a new reference or return existing if duplicate found.

    Deduplication strategy:
    1. Compute dedup_hash from DOI (if available) or title+first_author
    2. Check if reference with same hash exists
    3. If exists, return existing reference
    4. Otherwise, create new reference
    """
    # Compute dedup hash
    dedup_hash = compute_dedup_hash(
        title=payload.title, authors=payload.authors, doi=payload.doi
    )

    # Check if reference already exists
    existing_result = await db.execute(
        select(Reference).where(Reference.dedup_hash == dedup_hash)
    )
    existing_ref = existing_result.scalar_one_or_none()

    if existing_ref:
        # Reference already exists, return it
        return existing_ref

    # Create new reference
    reference = Reference(
        doi=payload.doi,
        title=payload.title,
        authors=payload.authors,
        source=payload.source,
        year=payload.year,
        url=payload.url,
        dedup_hash=dedup_hash,
    )
    db.add(reference)
    await db.commit()
    await db.refresh(reference)
    return reference


@router.get("/{reference_id}", response_model=ReferenceOut)
async def get_reference(reference_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific reference by ID."""
    reference = await db.get(Reference, reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Reference not found")
    return reference


@router.put("/{reference_id}", response_model=ReferenceOut)
async def update_reference(
    reference_id: int,
    payload: ReferenceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a reference."""
    reference = await db.get(Reference, reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Reference not found")

    data = payload.model_dump(exclude_unset=True)

    # Recalculate dedup_hash if title, authors, or doi changed
    if "title" in data or "authors" in data or "doi" in data:
        new_title = data.get("title", reference.title)
        new_authors = data.get("authors", reference.authors)
        new_doi = data.get("doi", reference.doi)
        data["dedup_hash"] = compute_dedup_hash(
            title=new_title, authors=new_authors, doi=new_doi
        )

    for field, value in data.items():
        setattr(reference, field, value)

    await db.commit()
    await db.refresh(reference)
    return reference


@router.delete("/{reference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reference(reference_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a reference."""
    reference = await db.get(Reference, reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Reference not found")

    await db.delete(reference)
    await db.commit()
    return None


@router.post("/bulk", response_model=List[ReferenceOut])
async def bulk_create_references(
    payload: List[ReferenceCreate], db: AsyncSession = Depends(get_db)
):
    """
    Bulk create references with automatic deduplication.

    Returns list of reference IDs (existing or newly created).
    """
    results = []

    for ref_data in payload:
        # Compute dedup hash
        dedup_hash = compute_dedup_hash(
            title=ref_data.title, authors=ref_data.authors, doi=ref_data.doi
        )

        # Check if exists
        existing_result = await db.execute(
            select(Reference).where(Reference.dedup_hash == dedup_hash)
        )
        existing_ref = existing_result.scalar_one_or_none()

        if existing_ref:
            results.append(existing_ref)
        else:
            # Create new
            reference = Reference(
                doi=ref_data.doi,
                title=ref_data.title,
                authors=ref_data.authors,
                source=ref_data.source,
                year=ref_data.year,
                url=ref_data.url,
                dedup_hash=dedup_hash,
            )
            db.add(reference)
            await db.flush()  # Flush to get ID
            results.append(reference)

    await db.commit()
    return results
