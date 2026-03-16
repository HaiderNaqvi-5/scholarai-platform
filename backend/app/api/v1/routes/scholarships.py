import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import RecordState, Scholarship
from app.schemas import (
    ScholarshipDetailResponse,
    ScholarshipListItem,
    ScholarshipListResponse,
)
from app.services.recommendations.eligibility import scholarship_in_scope

router = APIRouter()


@router.get("", response_model=ScholarshipListResponse)
async def list_scholarships(
    db: Annotated[AsyncSession, Depends(get_db)],
    query: str | None = Query(default=None, min_length=2, max_length=120),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    field_tag: str | None = Query(default=None, min_length=2, max_length=64),
    degree_level: str | None = Query(default=None, min_length=2, max_length=16),
    deadline_within_days: int | None = Query(default=None, ge=1, le=365),
    sort: str = Query(default="deadline"),
    limit: int = Query(default=25, ge=1, le=50),
) -> ScholarshipListResponse:
    normalized_sort = sort.strip().lower()
    if normalized_sort not in {"deadline", "title", "recent"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sort must be one of deadline, title, or recent",
        )

    statement = select(Scholarship).where(
        Scholarship.record_state == RecordState.PUBLISHED
    )

    if country_code:
        statement = statement.where(Scholarship.country_code == country_code.upper())

    result = await db.execute(statement)
    normalized_query = query.strip().lower() if query else None
    normalized_field_tag = field_tag.strip().lower() if field_tag else None
    normalized_degree_level = degree_level.strip().upper() if degree_level else None
    deadline_cutoff = None
    if deadline_within_days is not None:
        deadline_cutoff = datetime.now(timezone.utc) + timedelta(days=deadline_within_days)

    scholarships = []
    for scholarship in result.scalars().all():
        if not scholarship_in_scope(scholarship):
            continue
        if normalized_query and not matches_query(scholarship, normalized_query):
            continue
        if normalized_field_tag and not matches_field_tag(scholarship, normalized_field_tag):
            continue
        if normalized_degree_level and normalized_degree_level not in [
            value.upper() for value in scholarship.degree_levels
        ]:
            continue
        if deadline_cutoff is not None:
            if scholarship.deadline_at is None or scholarship.deadline_at > deadline_cutoff:
                continue
        scholarships.append(scholarship)

    scholarships = sort_scholarships(scholarships, normalized_sort)[:limit]
    items = [_serialize_list_item(scholarship) for scholarship in scholarships]
    return ScholarshipListResponse(
        items=items,
        total=len(items),
        applied_country_code=country_code.upper() if country_code else None,
        applied_query=query.strip() if query else None,
        applied_field_tag=field_tag.strip() if field_tag else None,
        applied_degree_level=normalized_degree_level,
        applied_deadline_within_days=deadline_within_days,
        applied_sort=normalized_sort,
    )


@router.get("/{scholarship_id}", response_model=ScholarshipDetailResponse)
async def get_scholarship(
    scholarship_id: uuid.UUID,
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


def matches_query(scholarship: Scholarship, normalized_query: str) -> bool:
    searchable = " ".join(
        filter(
            None,
            [
                scholarship.title,
                scholarship.provider_name,
                scholarship.summary,
                scholarship.funding_summary,
                " ".join(scholarship.field_tags),
            ],
        )
    ).lower()
    return normalized_query in searchable


def matches_field_tag(scholarship: Scholarship, normalized_field_tag: str) -> bool:
    normalized_tags = [tag.lower() for tag in scholarship.field_tags]
    return any(
        normalized_field_tag in tag or tag in normalized_field_tag
        for tag in normalized_tags
    )


def sort_scholarships(scholarships: list[Scholarship], sort: str) -> list[Scholarship]:
    if sort == "recent":
        return sorted(
            scholarships,
            key=lambda scholarship: scholarship.created_at,
            reverse=True,
        )
    if sort == "title":
        return sorted(scholarships, key=lambda scholarship: scholarship.title.lower())
    return sorted(
        scholarships,
        key=lambda scholarship: (
            scholarship.deadline_at is None,
            scholarship.deadline_at or datetime.max.replace(tzinfo=timezone.utc),
            scholarship.title.lower(),
        ),
    )
