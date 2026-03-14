"""
Scholarships routes: list, search, detail, recommendations.
"""
import uuid
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models.models import Scholarship, StudentProfile, MatchScore, EligibilityRequirement
from app.api.v1.schemas import (
    ScholarshipResponse, ScholarshipListItem, MatchScoreResponse, PaginatedResponse
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_scholarships(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    country: Optional[str] = Query(None),
    degree_level: Optional[str] = Query(None),
    field_of_study: Optional[str] = Query(None),
    is_active: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List scholarships with optional filters."""
    filters = [Scholarship.is_active == is_active]
    if country:
        filters.append(Scholarship.country.ilike(f"%{country}%"))
    if degree_level:
        filters.append(Scholarship.degree_levels.any(degree_level))
    if field_of_study:
        filters.append(Scholarship.field_of_study.any(f"%{field_of_study}%"))

    count_result = await db.execute(
        select(func.count()).select_from(Scholarship).where(and_(*filters))
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Scholarship)
        .where(and_(*filters))
        .order_by(Scholarship.deadline.asc().nulls_last())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    scholarships = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ScholarshipListItem.model_validate(s) for s in scholarships],
    )


@router.get("/recommendations", response_model=List[MatchScoreResponse])
async def get_recommendations(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
):
    """Return precomputed AI match scores for the current student.

    If no scores exist yet (new profile), returns empty list.
    The actual scoring is computed by the Celery task `compute_match_scores`.
    """
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complete your student profile first to receive recommendations",
        )

    scores_result = await db.execute(
        select(MatchScore)
        .where(MatchScore.student_id == profile.id)
        .order_by(MatchScore.overall_score.desc())
        .limit(limit)
        .options(selectinload(MatchScore.scholarship))
    )
    scores = scores_result.scalars().all()

    return [
        MatchScoreResponse(
            scholarship=ScholarshipListItem.model_validate(ms.scholarship),
            overall_score=float(ms.overall_score),
            success_probability=float(ms.success_probability) if ms.success_probability else None,
            vector_similarity=float(ms.vector_similarity) if ms.vector_similarity else None,
            feature_contributions=ms.feature_contributions,
        )
        for ms in scores
    ]


@router.get("/{scholarship_id}", response_model=ScholarshipResponse)
async def get_scholarship(
    scholarship_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get full scholarship detail including eligibility requirements."""
    result = await db.execute(
        select(Scholarship)
        .where(Scholarship.id == scholarship_id)
        .options(selectinload(Scholarship.eligibility_requirements))
    )
    scholarship = result.scalar_one_or_none()
    if not scholarship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship not found")
    return scholarship
