"""Schemas for POST /api/v1/scholarships/match (Feature 5, PRD §5).

Q1 retier (Task 7): the public response surface exposes only neutral fields
(id, name, provider, country_code, funding_amount, deadline, compatibility,
locked). Internal bucket labels never leak. The richer internal card type
``ScholarshipMatchCard`` is kept for service-internal sorting and for the
strategy report's "top 3" path; it is not serialised on the public API.
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScholarshipMatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # All fields optional — server auto-populates from the authenticated
    # student profile when omitted. Body fields override profile values.
    cgpa: float | None = Field(default=None, ge=0, le=4.0)
    degree_target: str | None = Field(default=None, max_length=8)
    fields: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    has_ielts: bool | None = None
    ielts_score: float | None = Field(default=None, ge=0, le=9)
    has_gre: bool | None = None
    funding_requirement: str | None = Field(default=None, max_length=32)
    nationality: str | None = Field(default=None, min_length=2, max_length=2)


# ----------------------------------------------------------------------
# Internal card type — used inside the service for classification + sort,
# and consumed by the strategy report's _match_scholarships helper. NOT
# part of the public API surface (see ScholarshipMatchOut below).
# ----------------------------------------------------------------------


class ScholarshipMatchCard(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    scholarship_id: UUID
    title: str
    provider_name: str | None
    country_code: str
    deadline_at: datetime | None
    funding_type: str | None
    funding_amount_min: float | None
    funding_amount_max: float | None
    field_tags: list[str]
    degree_levels: list[str]
    citizenship_rules: list[str]
    min_gpa_value: float | None
    deadline_days: int | None
    match_score: int
    match_reason: str
    open_to_pakistanis: bool
    locked: bool = False
    visa_approval_rate_pk: float | None = None
    priority_alert_eligible: bool | None = None


class LockedScholarshipCard(BaseModel):
    """Legacy internal type retained for backwards-compatible imports.

    The new public response uses ``ScholarshipMatchOut`` with ``locked=True``
    rather than a separate row shape.
    """

    scholarship_id: UUID
    title: str
    country_code: str
    funding_type: str | None
    deadline_days: int | None
    locked: bool = True


class UpgradePromptPayload(BaseModel):
    """Legacy free-tier upgrade payload (kept for callers / older clients)."""

    required_plan: list[str]
    price: str
    message: str


# ----------------------------------------------------------------------
# Public response surface — neutral, no internal vocabulary.
# ----------------------------------------------------------------------


class ScholarshipMatchOut(BaseModel):
    """One match row exposed on the public API.

    All fields are neutral — no eligible/partial/stretch/premium/standard
    or bucket/tier vocabulary. When ``locked=True`` the identifying fields
    are blanked and the row is meant to render as a blurred upgrade card.
    """

    model_config = ConfigDict(from_attributes=False)

    id: UUID | None = None
    name: str
    provider: str
    country_code: str | None = None
    funding_amount: str | None = None
    deadline: date | None = None
    compatibility: float = Field(ge=0.0, le=1.0)
    locked: bool = False


class UnlockOffer(BaseModel):
    """Neutral upgrade nudge attached to a MatchResponse."""

    model_config = ConfigDict(from_attributes=False)

    to_plan: Literal["pro", "elite"]
    locked_count: int = Field(ge=0)
    headline: str
    message: str


class MatchResponse(BaseModel):
    """Public POST /scholarships/match response.

    Internal bucket labels never appear on this shape — only the neutral
    row fields plus an optional unlock offer.
    """

    model_config = ConfigDict(from_attributes=False)

    items: list[ScholarshipMatchOut]
    unlock_offer: UnlockOffer | None = None


# Backwards-compatible alias so existing imports / FastAPI route response
# models (`response_model=ScholarshipMatchResponse`) continue to resolve
# to the new neutral shape. Old field names (eligible/partially_eligible/
# stretch/locked/visible_limit/...) are intentionally gone.
ScholarshipMatchResponse = MatchResponse
