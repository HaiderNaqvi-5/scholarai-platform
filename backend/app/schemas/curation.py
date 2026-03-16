from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CurationActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = Field(default=None, max_length=2000)


class CurationRawImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(min_length=3, max_length=64)
    source_display_name: str = Field(min_length=3, max_length=255)
    source_base_url: str = Field(min_length=8, max_length=2000)
    source_type: str = Field(default="manual_import", max_length=64)
    title: str = Field(min_length=3, max_length=255)
    provider_name: str | None = Field(default=None, max_length=255)
    country_code: str = Field(min_length=2, max_length=2)
    source_url: str = Field(min_length=8, max_length=2000)
    external_source_id: str | None = Field(default=None, max_length=255)
    source_document_ref: str | None = Field(default=None, max_length=255)
    summary: str | None = Field(default=None, max_length=4000)
    funding_summary: str | None = Field(default=None, max_length=2000)
    field_tags: list[str] = Field(default_factory=list)
    degree_levels: list[str] = Field(default_factory=lambda: ["MS"])
    citizenship_rules: list[str] = Field(default_factory=list)
    min_gpa_value: float | None = Field(default=None, ge=0, le=4.0)
    deadline_at: datetime | None = None
    imported_at: datetime | None = None
    source_last_seen_at: datetime | None = None
    review_notes: str | None = Field(default=None, max_length=2000)
    provenance_payload: dict | None = None

    @field_validator("country_code")
    @classmethod
    def normalize_import_country_code(cls, value: str) -> str:
        return value.upper()


class IngestionRunStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(min_length=3, max_length=64)
    source_display_name: str | None = Field(default=None, min_length=3, max_length=255)
    source_base_url: str | None = Field(default=None, min_length=8, max_length=2000)
    source_type: str = Field(default="official", max_length=64)
    max_records: int = Field(default=5, ge=1, le=20)


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
    total: int = Field(ge=0)
    applied_state: str | None = None


class IngestionRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    source_key: str
    source_display_name: str
    fetch_url: str
    status: str
    capture_mode: str | None
    parser_name: str | None
    records_found: int
    records_created: int
    records_skipped: int
    failure_reason: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class IngestionRunDetail(IngestionRunSummary):
    run_metadata: dict | None


class IngestionRunListResponse(BaseModel):
    items: list[IngestionRunSummary]
    total: int = Field(ge=0)
