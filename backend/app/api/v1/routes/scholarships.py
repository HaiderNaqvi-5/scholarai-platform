import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.core.plan_guard import can_see_premium, raise_plan_required
from app.models import RecordState, Scholarship, ScholarshipRequirement, ScholarshipTier, User
from app.schemas import (
    ScholarshipAppliedFilters,
    ScholarshipDetailResponse,
    ScholarshipListItem,
    ScholarshipListResponse,
    ScholarshipProvenanceResponse,
)
from app.schemas.scholarships_match import (
    ScholarshipMatchRequest,
    ScholarshipMatchResponse,
)
from app.services.ingestion import IngestionService
from app.services.recommendations.eligibility import scholarship_in_scope
from app.services.scholarships import ScholarshipMatchService
from app.services.students import StudentService

router = APIRouter()


async def get_optional_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Return the authenticated user when a valid bearer token is present.

    Anonymous callers receive ``None`` so public endpoints can downgrade to
    standard-tier-only views without forcing auth.  Any failure to decode the
    token (missing header, malformed, expired) is swallowed — callers should
    treat ``None`` as "anonymous", not "auth failed".
    """
    authorization = request.headers.get("Authorization") or request.headers.get("authorization")
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        return await get_current_user(token=token, db=db)
    except Exception:  # noqa: BLE001 — anon path swallows every auth failure
        return None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


@router.get("", response_model=ScholarshipListResponse)
async def list_scholarships(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: OptionalUser,
    query: str | None = Query(default=None, min_length=2, max_length=120),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    field_tag: str | None = Query(default=None, min_length=2, max_length=64),
    degree_level: str | None = Query(default=None, min_length=2, max_length=16),
    provider: str | None = Query(default=None, min_length=2, max_length=120),
    funding_type: str | None = Query(default=None, min_length=2, max_length=64),
    min_amount: float | None = Query(default=None, ge=0),
    max_amount: float | None = Query(default=None, ge=0),
    has_deadline: bool | None = Query(default=None),
    deadline_within_days: int | None = Query(default=None, ge=1, le=365),
    deadline_after: datetime | None = Query(default=None),
    deadline_before: datetime | None = Query(default=None),
    sort: str = Query(default="deadline"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
) -> ScholarshipListResponse:
    normalized_sort = sort.strip().lower()
    if normalized_sort not in {"deadline", "title", "recent"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Sort must be one of deadline, title, or recent",
                "field": "sort",
                "allowed_values": ["deadline", "title", "recent"],
                "received": sort,
            },
        )

    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Minimum amount cannot be greater than maximum amount",
                "field": "min_amount",
                "min_amount": min_amount,
                "max_amount": max_amount,
            },
        )

    statement = select(Scholarship).where(
        Scholarship.record_state == RecordState.PUBLISHED
    )
    if current_user is None or not can_see_premium(current_user):
        statement = statement.where(Scholarship.tier == ScholarshipTier.STANDARD)
    if country_code:
        statement = statement.where(Scholarship.country_code == country_code.upper())

    result = await db.execute(statement)
    scholarships = []

    normalized_query = query.strip().lower() if query else None
    normalized_field_tag = field_tag.strip().lower() if field_tag else None
    normalized_degree_level = degree_level.strip().upper() if degree_level else None
    normalized_provider = provider.strip().lower() if provider else None
    normalized_funding_type = funding_type.strip().lower() if funding_type else None
    deadline_cutoff = (
        datetime.now(timezone.utc) + timedelta(days=deadline_within_days)
        if deadline_within_days is not None
        else None
    )

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
        if normalized_provider and not matches_provider(scholarship, normalized_provider):
            continue
        if normalized_funding_type and (scholarship.funding_type or "").lower() != normalized_funding_type:
            continue
        if min_amount is not None or max_amount is not None:
            if not matches_amount_window(scholarship, min_amount=min_amount, max_amount=max_amount):
                continue
        if has_deadline is not None and not matches_has_deadline(scholarship, has_deadline):
            continue
        if deadline_cutoff is not None and not matches_deadline_cutoff(scholarship, deadline_cutoff):
            continue
        if deadline_after is not None and not matches_deadline_after(scholarship, deadline_after):
            continue
        if deadline_before is not None and not matches_deadline_before(scholarship, deadline_before):
            continue
        scholarships.append(scholarship)

    scholarships = sort_scholarships(scholarships, normalized_sort)
    total = len(scholarships)
    start = (page - 1) * page_size
    end = start + page_size
    items = [_serialize_list_item(scholarship) for scholarship in scholarships[start:end]]

    return ScholarshipListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
        applied_filters=ScholarshipAppliedFilters(
            country_code=country_code.upper() if country_code else None,
            query=query.strip() if query else None,
            field_tag=field_tag.strip() if field_tag else None,
            degree_level=normalized_degree_level,
            provider=provider.strip() if provider else None,
            funding_type=funding_type.strip().lower() if funding_type else None,
            min_amount=min_amount,
            max_amount=max_amount,
            has_deadline=has_deadline,
            deadline_within_days=deadline_within_days,
            deadline_after=deadline_after,
            deadline_before=deadline_before,
            sort=normalized_sort,
        ),
    )


@router.post("/match", response_model=ScholarshipMatchResponse)
async def match_scholarships(
    payload: ScholarshipMatchRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScholarshipMatchResponse:
    """Pakistan-tuned scholarship matching (PRD §5).

    Auto-populates eligibility criteria from the authenticated student profile.
    Body fields override profile values. Free-tier callers receive only the
    top 3 eligible matches in full plus a locked summary list.
    """
    profile = await StudentService(db).get_profile(current_user.id)
    service = ScholarshipMatchService(db)
    return await service.match(current_user, profile, payload)


@router.get("/{scholarship_id}", response_model=ScholarshipDetailResponse)
async def get_scholarship(
    scholarship_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: OptionalUser,
) -> ScholarshipDetailResponse:
    result = await db.execute(
        select(Scholarship)
        .where(
            Scholarship.id == scholarship_id,
            Scholarship.record_state == RecordState.PUBLISHED,
        )
        .options(selectinload(Scholarship.requirements), selectinload(Scholarship.source_registry))
    )
    scholarship = result.scalar_one_or_none()
    if scholarship is None or not scholarship_in_scope(scholarship):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published scholarship not found",
        )
    _guard_premium_tier(scholarship, current_user)

    return ScholarshipDetailResponse(
        **_serialize_list_item(scholarship).model_dump(),
        summary=scholarship.summary,
        funding_summary=scholarship.funding_summary,
        funding_type=scholarship.funding_type,
        funding_amount_min=float(scholarship.funding_amount_min)
        if scholarship.funding_amount_min is not None
        else None,
        funding_amount_max=float(scholarship.funding_amount_max)
        if scholarship.funding_amount_max is not None
        else None,
        source_url=scholarship.source_url,
        field_tags=scholarship.field_tags,
        degree_levels=scholarship.degree_levels,
        citizenship_rules=scholarship.citizenship_rules,
        min_gpa_value=float(scholarship.min_gpa_value)
        if scholarship.min_gpa_value is not None
        else None,
        source_document_ref=scholarship.source_document_ref,
        requirement_summary=build_requirement_summary(scholarship.requirements),
        last_validated_at=scholarship.validated_at,
        published_at=scholarship.published_at,
        publication_hint=build_publication_hint(scholarship),
    )


@router.get(
    "/{scholarship_id}/provenance",
    response_model=ScholarshipProvenanceResponse,
)
async def get_scholarship_provenance(
    scholarship_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: OptionalUser,
) -> ScholarshipProvenanceResponse:
    """Trace a published scholarship back to its ingestion source + run.

    Published-only — non-published records return 404, preserving the
    published-only contract of the public scholarships surface. Premium-tier
    rows are paywalled the same way as the detail endpoint: anonymous → 401,
    free → 402 with the standard upgrade payload.
    """
    scholarship = await db.execute(
        select(Scholarship.tier).where(Scholarship.id == scholarship_id)
    )
    tier_row = scholarship.scalar_one_or_none()
    if tier_row is not None:
        # synthetic shim so _guard_premium_tier can read .tier
        _guard_premium_tier(_TierOnly(tier_row), current_user)
    return await IngestionService(db).trace_provenance(
        scholarship_id, require_published=True
    )


class _TierOnly:
    """Lightweight stand-in exposing only ``.tier`` for the premium guard."""

    __slots__ = ("tier",)

    def __init__(self, tier: ScholarshipTier) -> None:
        self.tier = tier


def _guard_premium_tier(scholarship: Scholarship | _TierOnly, current_user: User | None) -> None:
    """Raise 402 (or 401 for anon) when a premium-tier row is being requested
    by a caller whose plan cannot view premium scholarships.

    Free / anonymous → blocked. Pro / Elite / Institution → allowed.
    """
    if scholarship.tier != ScholarshipTier.PREMIUM:
        return
    if current_user is None:
        # Anonymous caller — no upgrade payload makes sense without a plan_currency,
        # so surface a generic 402 that prompts sign-in + upgrade.
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "plan_required",
                "required_plan": ["pro", "elite"],
                "current_plan": None,
                "upgrade_url": "/upgrade",
                "message": "Sign in with a Pro or Elite plan to view this scholarship's full details.",
            },
        )
    if can_see_premium(current_user):
        return
    raise_plan_required(
        current_user,
        ["pro", "elite"],
        message="Upgrade to Pro to view this scholarship's full details.",
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
                scholarship.funding_type,
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


def matches_provider(scholarship: Scholarship, normalized_provider: str) -> bool:
    return normalized_provider in (scholarship.provider_name or "").lower()


def matches_amount_window(
    scholarship: Scholarship,
    *,
    min_amount: float | None,
    max_amount: float | None,
) -> bool:
    if scholarship.funding_amount_min is None and scholarship.funding_amount_max is None:
        return False

    available_min = float(scholarship.funding_amount_min or scholarship.funding_amount_max)
    available_max = float(scholarship.funding_amount_max or scholarship.funding_amount_min)

    if min_amount is not None and available_max < min_amount:
        return False
    if max_amount is not None and available_min > max_amount:
        return False
    return True


def matches_has_deadline(scholarship: Scholarship, has_deadline: bool) -> bool:
    return (scholarship.deadline_at is not None) is has_deadline


def matches_deadline_cutoff(scholarship: Scholarship, deadline_cutoff: datetime) -> bool:
    return scholarship.deadline_at is not None and scholarship.deadline_at <= deadline_cutoff


def matches_deadline_after(scholarship: Scholarship, deadline_after: datetime) -> bool:
    return scholarship.deadline_at is not None and scholarship.deadline_at >= deadline_after


def matches_deadline_before(scholarship: Scholarship, deadline_before: datetime) -> bool:
    return scholarship.deadline_at is not None and scholarship.deadline_at <= deadline_before


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


def build_requirement_summary(requirements: list[ScholarshipRequirement]) -> list[str]:
    if not requirements:
        return ["No structured requirement rows were published for this record."]

    summary = []
    for requirement in requirements:
        value = requirement.value_text or "Structured value available"
        label = requirement.requirement_type.value.replace("_", " ")
        summary.append(f"{label.title()} {requirement.operator} {value}")
    return summary


def build_publication_hint(scholarship: Scholarship) -> str:
    source_name = scholarship.source_registry.display_name if scholarship.source_registry else "the linked source registry"
    if scholarship.validated_at and scholarship.published_at:
        return (
            f"Published from a validated record after curator review. Last validation was "
            f"{scholarship.validated_at.date().isoformat()} against {source_name}."
        )
    if scholarship.published_at:
        return f"Published for student-facing use and linked back to {source_name}."
    return "Published for student-facing use. Validation timing is not available on this record."
