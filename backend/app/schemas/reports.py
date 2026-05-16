"""Schemas for the Elite application strategy report (PRD §0.6)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrategyReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # All optional — the report is built from the authenticated student's
    # saved profile. Body fields are reserved for future per-run overrides.
    notes: str | None = Field(default=None, max_length=500)


class ReportProfileSummary(BaseModel):
    full_name: str | None
    pakistani_university: str | None
    cgpa_value: float | None
    cgpa_us_equivalent: float | None
    uk_degree_class: str | None
    ielts_score: float | None
    target_degree: str | None
    target_countries: list[str]
    target_fields: list[str]
    funding_requirement: str | None


class ReportUniversityMatch(BaseModel):
    university_id: UUID
    name: str
    country: str
    tier: Literal["Safety", "Target", "Reach"]
    reason: str


class ReportScholarshipMatch(BaseModel):
    scholarship_id: UUID
    title: str
    country_code: str
    funding_type: str | None
    deadline_days: int | None
    match_reason: str


class ReportActionPlan(BaseModel):
    next_30_days: list[str]
    next_60_days: list[str]
    next_90_days: list[str]


class StrategyReportResponse(BaseModel):
    document_id: UUID
    document_type: str = "strategy_report"
    profile_summary: ReportProfileSummary
    universities: list[ReportUniversityMatch]
    scholarships: list[ReportScholarshipMatch]
    action_plan: ReportActionPlan
    generated_guidance: str
    limitations: str
    used_llm: bool
    created_at: datetime
