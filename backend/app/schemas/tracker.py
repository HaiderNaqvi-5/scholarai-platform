"""Schemas for /api/v1/tracker (Feature 6, PRD §6)."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TRACKER_STAGES


_DEFAULT_CHECKLIST_KEYS = {
    "transcripts",
    "degree_certificate",
    "ielts_certificate",
    "gre_scores",
    "sop_draft",
    "sop_final",
    "cv_resume",
    "lor_1",
    "lor_2",
    "lor_3",
    "bank_statement",
    "hec_attestation",
    "passport_copy",
    "application_fee_paid",
}


class TrackerItemCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scholarship_id: UUID | None = None
    university_id: UUID | None = None
    program_name: str | None = Field(default=None, max_length=255)
    university_name: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    stage: str = Field(default="researching", max_length=32)
    deadline: date | None = None
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("stage")
    @classmethod
    def stage_allowed(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in TRACKER_STAGES:
            raise ValueError(f"stage must be one of: {', '.join(TRACKER_STAGES)}")
        return value

    @field_validator("country")
    @classmethod
    def country_uppercase(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class TrackerStageUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage: str

    @field_validator("stage")
    @classmethod
    def stage_allowed(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in TRACKER_STAGES:
            raise ValueError(f"stage must be one of: {', '.join(TRACKER_STAGES)}")
        return value


class TrackerChecklistPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checklist: dict[str, bool]

    @field_validator("checklist")
    @classmethod
    def reject_unknown_keys(cls, value: dict[str, bool]) -> dict[str, bool]:
        unknown = set(value.keys()) - _DEFAULT_CHECKLIST_KEYS
        if unknown:
            raise ValueError(f"unknown checklist keys: {', '.join(sorted(unknown))}")
        return value


class TrackerItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    scholarship_id: UUID | None
    university_id: UUID | None
    program_name: str | None
    university_name: str | None
    country: str | None
    stage: str
    deadline: date | None
    notes: str | None
    document_checklist: dict[str, bool]
    created_at: datetime
    updated_at: datetime


class TrackerListResponse(BaseModel):
    items: list[TrackerItemResponse]
    total: int
    plan_limit: int | None = None
    plan: str
