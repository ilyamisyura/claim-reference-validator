from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_db
from app.models.claim import Claim
from app.models.claim_reference import ClaimReference
from app.models.project import Project
from app.models.reference import Reference
from app.schemas.claim import ClaimCreate, ClaimOut, ClaimUpdate, ClaimWithReferences
from app.schemas.pagination import PaginatedResponse


router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("/", response_model=PaginatedResponse[ClaimOut])
async def list_claims(
    project_id: int | None = Query(None, description="Filter by project ID"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """List claims with optional filtering by project."""
    # Build query
    query = select(Claim)
    if project_id:
        query = query.where(Claim.project_id == project_id)

    # Get total count
    count_query = select(func.count()).select_from(Claim)
    if project_id:
        count_query = count_query.where(Claim.project_id == project_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Calculate offset
    offset = (page - 1) * page_size

    # Get paginated results
    result = await db.execute(
        query.order_by(Claim.created_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    # Add reference IDs to each claim
    claims_out = []
    for claim in items:
        claim_refs_result = await db.execute(
            select(ClaimReference.reference_id).where(
                ClaimReference.claim_id == claim.id
            )
        )
        reference_ids = [r[0] for r in claim_refs_result.all()]

        claim_dict = ClaimOut.model_validate(claim).model_dump()
        claim_dict["references"] = reference_ids
        claims_out.append(ClaimOut(**claim_dict))

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=claims_out,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=ClaimOut, status_code=status.HTTP_201_CREATED)
async def create_claim(payload: ClaimCreate, db: AsyncSession = Depends(get_db)):
    """Create a new claim and optionally link it to references."""
    # Verify project exists
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify all reference IDs exist
    if payload.reference_ids:
        refs_result = await db.execute(
            select(Reference).where(Reference.id.in_(payload.reference_ids))
        )
        existing_refs = refs_result.scalars().all()
        if len(existing_refs) != len(payload.reference_ids):
            raise HTTPException(status_code=404, detail="One or more references not found")

    # Create claim
    claim = Claim(
        project_id=payload.project_id,
        text=payload.text,
        claim_type=payload.claim_type,
        page_number=payload.page_number,
        paragraph_index=payload.paragraph_index,
    )
    db.add(claim)
    await db.flush()  # Flush to get claim ID

    # Link references
    for ref_id in payload.reference_ids:
        claim_ref = ClaimReference(claim_id=claim.id, reference_id=ref_id)
        db.add(claim_ref)

    await db.commit()
    await db.refresh(claim)

    # Return with reference IDs
    claim_out = ClaimOut.model_validate(claim)
    claim_out.references = payload.reference_ids
    return claim_out


@router.get("/{claim_id}", response_model=ClaimWithReferences)
async def get_claim(claim_id: int, db: AsyncSession = Depends(get_db)):
    """Get a claim with full reference details."""
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Get references
    refs_result = await db.execute(
        select(Reference)
        .join(ClaimReference, ClaimReference.reference_id == Reference.id)
        .where(ClaimReference.claim_id == claim_id)
    )
    references = refs_result.scalars().all()

    claim_dict = ClaimOut.model_validate(claim).model_dump()
    claim_dict["references"] = [r.id for r in references]
    claim_dict["reference_details"] = references

    return ClaimWithReferences(**claim_dict)


@router.put("/{claim_id}", response_model=ClaimOut)
async def update_claim(
    claim_id: int,
    payload: ClaimUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a claim."""
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(claim, field, value)

    await db.commit()
    await db.refresh(claim)

    # Get reference IDs
    refs_result = await db.execute(
        select(ClaimReference.reference_id).where(ClaimReference.claim_id == claim.id)
    )
    reference_ids = [r[0] for r in refs_result.all()]

    claim_out = ClaimOut.model_validate(claim)
    claim_out.references = reference_ids
    return claim_out


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(claim_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a claim."""
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    await db.delete(claim)
    await db.commit()
    return None


@router.post("/{claim_id}/references/{reference_id}", response_model=ClaimOut)
async def link_claim_to_reference(
    claim_id: int,
    reference_id: int,
    relevance_score: float | None = Query(None, ge=0, le=1),
    context: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Link a claim to a reference."""
    # Verify claim exists
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Verify reference exists
    reference = await db.get(Reference, reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Reference not found")

    # Check if link already exists
    existing_result = await db.execute(
        select(ClaimReference).where(
            ClaimReference.claim_id == claim_id,
            ClaimReference.reference_id == reference_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Update existing link
        if relevance_score is not None:
            existing.relevance_score = relevance_score
        if context is not None:
            existing.context = context
    else:
        # Create new link
        claim_ref = ClaimReference(
            claim_id=claim_id,
            reference_id=reference_id,
            relevance_score=relevance_score,
            context=context,
        )
        db.add(claim_ref)

    await db.commit()

    # Return claim with references
    refs_result = await db.execute(
        select(ClaimReference.reference_id).where(ClaimReference.claim_id == claim_id)
    )
    reference_ids = [r[0] for r in refs_result.all()]

    claim_out = ClaimOut.model_validate(claim)
    claim_out.references = reference_ids
    return claim_out


@router.delete("/{claim_id}/references/{reference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_claim_from_reference(
    claim_id: int,
    reference_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Unlink a claim from a reference."""
    result = await db.execute(
        select(ClaimReference).where(
            ClaimReference.claim_id == claim_id,
            ClaimReference.reference_id == reference_id,
        )
    )
    claim_ref = result.scalar_one_or_none()

    if not claim_ref:
        raise HTTPException(status_code=404, detail="Link not found")

    await db.delete(claim_ref)
    await db.commit()
    return None
