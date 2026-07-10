"""Waitlist + upgrade-pricing REST surface (Feature 10)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.models import Waitlist
from app.schemas.waitlist import (
    PricingResponse,
    PricingTier,
    WaitlistJoinRequest,
    WaitlistJoinResponse,
)
from app.services.notifications.channels import send_templated_email_best_effort

# P2-16: anti-abuse cap on the public join endpoint. IP-keyed (no auth on this
# route) via app.core.rate_limit._subject's unauthenticated fallback.
_WAITLIST_RATE_LIMIT = RateLimiter(requests_limit=5, window_seconds=3_600, fail_open=False)


router = APIRouter()


_PRICING_BY_CURRENCY = {
    "PKR": {"pro": "PKR 2,999/month", "elite": "PKR 6,000/month", "institution": "Custom annual"},
    "GBP": {"pro": "£8.49/month",     "elite": "£16.99/month",    "institution": "Custom annual"},
    "EUR": {"pro": "€9.49/month",     "elite": "€18.99/month",    "institution": "Custom annual"},
    "AED": {"pro": "AED 39/month",    "elite": "AED 79/month",    "institution": "Custom annual"},
    "USD": {"pro": "$9.99/month",     "elite": "$19.99/month",    "institution": "Custom annual"},
}


def _build_tiers(currency: str) -> list[PricingTier]:
    prices = _PRICING_BY_CURRENCY[currency]
    return [
        PricingTier(
            key="explorer",
            label="Explorer",
            is_recommended=False,
            monthly_price="Free",
            yearly_hint=None,
            feature_summary="Curious students, habit-building.",
            bullet_features=[
                "Top 3 scholarship matches",
                "Top 3 university matches",
                "1 SOP draft, lifetime",
                "Visa interview Q1–Q3 free",
                "Track up to 3 applications",
                "Deadline reminders active for first 30 days",
            ],
        ),
        PricingTier(
            key="pro",
            label="Pro",
            is_recommended=True,
            monthly_price=prices["pro"],
            yearly_hint="Less than one consultant meeting.",
            feature_summary="Serious applicants in Pakistan.",
            bullet_features=[
                "5 SOP drafts per month",
                "Full match list — 6 personalised scholarships",
                "6 university matches",
                "Full 10-question visa interview sessions",
                "6-card application tracker",
                "Email deadline reminders",
            ],
        ),
        PricingTier(
            key="elite",
            label="Elite",
            is_recommended=False,
            monthly_price=prices["elite"],
            yearly_hint="Less than a coffee per week for diaspora families.",
            feature_summary="Diaspora and high-stakes applicants.",
            bullet_features=[
                "10 SOP drafts per month with line-by-line AI feedback",
                "12 personalised scholarships — every match revealed",
                "12 university matches",
                "12-card application tracker",
                "Downloadable visa interview transcripts",
                "Professor cold-email generator",
                "Application strategy PDF report",
                "Priority WhatsApp deadline alerts",
            ],
        ),
        PricingTier(
            key="institution",
            label="Institution",
            is_recommended=False,
            monthly_price=prices["institution"],
            yearly_hint=None,
            feature_summary="Universities and Pakistani schools.",
            bullet_features=[
                "Bulk student enrolment",
                "Aggregate outcomes dashboard",
                "Co-branded career-centre portal",
                "Dedicated B2B data-share agreement",
            ],
        ),
    ]


@router.get("/upgrade/pricing", response_model=PricingResponse)
async def get_pricing(
    currency: str = Query(default="PKR", min_length=3, max_length=3),
    audience: str = Query(
        default="student",
        pattern="^(student|institution)$",
        description=(
            "Audience filter. PRD §0.6 trust boundary: the student-facing /upgrade"
            " page must never show the Institution tier. Use audience=institution"
            " only from /universities or the partners surface."
        ),
    ),
) -> PricingResponse:
    cur = currency.upper()
    if cur not in _PRICING_BY_CURRENCY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="currency must be PKR / GBP / EUR / AED / USD",
        )
    tiers = _build_tiers(cur)
    if audience == "student":
        # Trust boundary: Institution tier never appears in the student UI.
        tiers = [t for t in tiers if t.key != "institution"]
    return PricingResponse(currency=cur, tiers=tiers)


@router.post(
    "/waitlist",
    response_model=WaitlistJoinResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_WAITLIST_RATE_LIMIT)],
)
async def join_waitlist(
    payload: WaitlistJoinRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WaitlistJoinResponse:
    # P2-16: select-then-insert raced two concurrent joins for the same email
    # into an IntegrityError 500. ON CONFLICT DO UPDATE is atomic at the DB
    # level, so a duplicate join is a race-free upsert, not a crash.
    # (Waitlist has no updated_at column, so nothing else needs to be bumped.)
    stmt = (
        pg_insert(Waitlist)
        .values(email=payload.email, plan=payload.plan, currency=payload.currency, country=payload.country)
        .on_conflict_do_update(
            index_elements=["email"],
            set_={"plan": payload.plan, "currency": payload.currency, "country": payload.country},
        )
        .returning(Waitlist)
    )
    result = await db.execute(stmt)
    row = result.scalar_one()
    await db.commit()

    send_templated_email_best_effort(
        to=row.email,
        template="waitlist_confirmation",
        context={"plan": row.plan, "currency": row.currency},
        source="waitlist",
    )
    return WaitlistJoinResponse(
        id=row.id,
        email=row.email,
        plan=row.plan,
        currency=row.currency,
        created_at=row.created_at,
    )
