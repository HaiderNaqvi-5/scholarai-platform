from datetime import datetime
from typing import Literal

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
    execution_mode: Literal["inline", "worker", "auto"] = "inline"


class IngestionRunRetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_records: int | None = Field(default=None, ge=1, le=20)
    execution_mode: Literal["inline"] | None = None


class IngestionRunQueueAssignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    queue_key: str = Field(min_length=2, max_length=64)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("queue_key")
    @classmethod
    def normalize_queue_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("queue_key must not be empty or only whitespace")
        return normalized


class IngestionRunBulkRetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_ids: list[str] = Field(min_length=1, max_length=50)
    max_records: int | None = Field(default=None, ge=1, le=20)
    execution_mode: Literal["inline"] | None = None

    @field_validator("run_ids")
    @classmethod
    def normalize_run_ids(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item and item.strip()]
        if not normalized:
            raise ValueError("run_ids must include at least one run id")
        return normalized


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
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    has_more: bool = False
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
    execution_mode_requested: str | None = None
    execution_mode_selected: str | None = None
    dispatch_status: str | None = None
    celery_task_id: str | None = None
    attempt_count: int | None = None
    run_retry_count: int | None = None
    last_started_at: str | None = None
    last_retry_requested_at: str | None = None
    failure_phase: str | None = None
    review_queue: str | None = None
    queue_assigned_by_user_id: str | None = None
    queue_assigned_at: str | None = None
    queue_assignment_note: str | None = None
    snapshot_available: bool = False
    snapshot_captured_at: str | None = None
    snapshot_content_length: int | None = None


class IngestionRunDetail(IngestionRunSummary):
    run_metadata: dict | None


class IngestionRunBulkRetryItem(BaseModel):
    run_id: str
    status: Literal["retried", "skipped", "failed"]
    message: str
    detail: IngestionRunDetail | None = None


class IngestionRunBulkRetryResponse(BaseModel):
    items: list[IngestionRunBulkRetryItem]
    total: int = Field(ge=0)
    retried: int = Field(ge=0)
    skipped: int = Field(ge=0)
    failed: int = Field(ge=0)


class IngestionRunSnapshotResponse(BaseModel):
    run_id: str
    available: bool
    html_content: str | None = None
    captured_at: str | None = None
    content_length: int | None = None
    truncated: bool = False


class IngestionRunListResponse(BaseModel):
    items: list[IngestionRunSummary]
    total: int = Field(ge=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    has_more: bool = False
