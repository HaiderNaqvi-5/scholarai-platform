from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CurationActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = Field(default=None, max_length=2000)


class CurationRecordUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=255)
    provider_name: str | None = Field(default=None, max_length=255)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    summary: str | None = Field(default=None, max_length=4000)
    funding_summary: str | None = Field(default=None, max_length=2000)
    source_document_ref: str | None = Field(default=None, max_length=255)
    deadline_at: datetime | None = None
    field_tags: list[str] | None = None
    degree_levels: list[str] | None = None
    citizenship_rules: list[str] | None = None
    min_gpa_value: float | None = Field(default=None, ge=0, le=4.0)
    review_notes: str | None = Field(default=None, max_length=2000)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class CurationRecordSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record_id: str
    title: str
    provider_name: str | None
    country_code: str
    record_state: str
    source_url: str
    source_type: str | None
    imported_at: datetime | None
    source_last_seen_at: datetime | None
    last_reviewed_at: datetime | None
    validated_at: datetime | None
    published_at: datetime | None
    review_notes: str | None


class CurationRecordDetail(CurationRecordSummary):
    summary: str | None
    funding_summary: str | None
    field_tags: list[str]
    degree_levels: list[str]
    citizenship_rules: list[str]
    min_gpa_value: float | None
    source_document_ref: str | None
    provenance_payload: dict | None
    reviewed_by_user_id: str | None
    validated_by_user_id: str | None
    published_by_user_id: str | None
    rejected_at: datetime | None
    unpublished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CurationRecordListResponse(BaseModel):
    items: list[CurationRecordSummary]
