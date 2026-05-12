"""Schemas for POST /api/v1/scholarships/match (Feature 5, PRD §5)."""

from datetime import datetime
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
    """Minimal payload shown to free-tier users for results 4+.
    Renders blurred on the frontend with the count + upgrade prompt."""

    scholarship_id: UUID
    title: str
    country_code: str
    funding_type: str | None
    deadline_days: int | None
    locked: bool = True


class UpgradePromptPayload(BaseModel):
    required_plan: list[str]
    price: str
    message: str


class ScholarshipMatchResponse(BaseModel):
    eligible: list[ScholarshipMatchCard]
    partially_eligible: list[ScholarshipMatchCard]
    stretch: list[ScholarshipMatchCard]
    locked: list[LockedScholarshipCard]
    total_found: int
    fully_funded_count: int
    visible_limit: int
    upgrade_prompt: UpgradePromptPayload | None = None
