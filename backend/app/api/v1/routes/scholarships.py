import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models import RecordState, Scholarship
from app.schemas import ScholarshipDetailResponse, ScholarshipListItem
from app.services.recommendations.eligibility import scholarship_in_scope

router = APIRouter()


@router.get("", response_model=list[ScholarshipListItem])
async def list_scholarships(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    limit: int = Query(default=25, ge=1, le=50),
) -> list[ScholarshipListItem]:
    query = (
        select(Scholarship)
        .where(Scholarship.record_state == RecordState.PUBLISHED)
        .order_by(Scholarship.deadline_at.asc().nulls_last(), Scholarship.title.asc())
        .limit(limit)
    )

    if country_code:
        query = query.where(Scholarship.country_code == country_code.upper())

    result = await db.execute(query)
    scholarships = [
        scholarship
        for scholarship in result.scalars().all()
        if scholarship_in_scope(scholarship)
    ]
    return [_serialize_list_item(scholarship) for scholarship in scholarships]


@router.get("/{scholarship_id}", response_model=ScholarshipDetailResponse)
async def get_scholarship(
    scholarship_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScholarshipDetailResponse:
    result = await db.execute(
        select(Scholarship)
        .where(
            Scholarship.id == scholarship_id,
            Scholarship.record_state == RecordState.PUBLISHED,
        )
        .options(selectinload(Scholarship.requirements))
    )
    scholarship = result.scalar_one_or_none()
    if scholarship is None or not scholarship_in_scope(scholarship):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published scholarship not found",
        )

    return ScholarshipDetailResponse(
        **_serialize_list_item(scholarship).model_dump(),
        summary=scholarship.summary,
        funding_summary=scholarship.funding_summary,
        source_url=scholarship.source_url,
        field_tags=scholarship.field_tags,
        degree_levels=scholarship.degree_levels,
        citizenship_rules=scholarship.citizenship_rules,
        min_gpa_value=float(scholarship.min_gpa_value)
        if scholarship.min_gpa_value is not None
        else None,
        source_document_ref=scholarship.source_document_ref,
    )


def _serialize_list_item(scholarship: Scholarship) -> ScholarshipListItem:
    return ScholarshipListItem(
        scholarship_id=str(scholarship.id),
        title=scholarship.title,
        provider_name=scholarship.provider_name,
        country_code=scholarship.country_code,
        deadline_at=scholarship.deadline_at,
        record_state=scholarship.record_state.value,
    )
