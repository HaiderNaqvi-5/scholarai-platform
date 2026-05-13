"""Waitlist + upgrade-pricing REST surface (Feature 10)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Waitlist
from app.schemas.waitlist import (
    PricingResponse,
    PricingTier,
    WaitlistJoinRequest,
    WaitlistJoinResponse,
)


router = APIRouter()


_PRICING_BY_CURRENCY = {
    "PKR": {
        "pro": "PKR 2,499/month",
        "elite": "PKR 7,999/month",
        "institution": "Custom annual",
    },
    "GBP": {"pro": "£6.99/month", "elite": "£19.99/month", "institution": "Custom annual"},
    "EUR": {"pro": "€7.99/month", "elite": "€22.99/month", "institution": "Custom annual"},
    "AED": {"pro": "AED 29/month", "elite": "AED 89/month", "institution": "Custom annual"},
    "USD": {"pro": "$8.99/month", "elite": "$24.99/month", "institution": "Custom annual"},
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
                "Unlimited scholarship and university matches",
                "Unlimited SOP drafts across programs",
                "Full 10-question visa interview sessions",
                "Unlimited application tracker",
                "Always-on email deadline reminders",
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
                "Line-by-line AI feedback on every SOP",
                "Downloadable visa interview transcripts",
                "Professor cold-email generator",
                "Application strategy PDF report",
                "Priority scholarship alerts via SMS + WhatsApp",
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
) -> PricingResponse:
    cur = currency.upper()
    if cur not in _PRICING_BY_CURRENCY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="currency must be PKR / GBP / EUR / AED / USD",
        )
    return PricingResponse(currency=cur, tiers=_build_tiers(cur))


@router.post("/waitlist", response_model=WaitlistJoinResponse, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    payload: WaitlistJoinRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WaitlistJoinResponse:
    result = await db.execute(select(Waitlist).where(Waitlist.email == payload.email))
    row = result.scalar_one_or_none()
    if row is None:
        row = Waitlist(email=payload.email)
        db.add(row)
    row.plan = payload.plan
    row.currency = payload.currency
    row.country = payload.country
    await db.flush()
    await db.refresh(row)
    await db.commit()
    return WaitlistJoinResponse(
        id=row.id,
        email=row.email,
        plan=row.plan,
        currency=row.currency,
        created_at=row.created_at,
    )
