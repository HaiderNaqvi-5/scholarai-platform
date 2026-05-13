"""Schemas for privacy + consent + B2B (Feature 9.5)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


_ALLOWED_CONSENT_TYPES = {"terms", "privacy", "marketing", "b2b_share", "cookies", "aup"}


class ConsentGrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consent_type: str
    version: str
    granted: bool

    @field_validator("consent_type")
    @classmethod
    def consent_type_allowed(cls, value: str) -> str:
        v = value.strip().lower()
        if v not in _ALLOWED_CONSENT_TYPES:
            raise ValueError("Unsupported consent_type")
        return v


class ConsentRecordResponse(BaseModel):
    consent_type: str
    version: str
    granted: bool
    granted_at: datetime | None


class ConsentStateResponse(BaseModel):
    records: list[ConsentRecordResponse]
    current_versions: dict[str, str]


class LegalDocumentResponse(BaseModel):
    slug: str
    version: str
    effective_at: datetime
    body_markdown: str
    sha256_hash: str


class DataExportResponse(BaseModel):
    id: UUID
    status: str
    requested_at: datetime
    completed_at: datetime | None
    download_url: str | None
    expires_at: datetime | None


class DataDeletionRequestResponse(BaseModel):
    id: UUID
    status: str
    requested_at: datetime
    scheduled_for: datetime
    cancelled_at: datetime | None
    executed_at: datetime | None


class DataDeletionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = Field(default=None, max_length=1000)


class B2BShareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_user_id: UUID
    university_id: UUID
    institution_id: UUID | None = None
    share_reason: str
    shared_with_email: str | None = Field(default=None, max_length=255)


class B2BShareResponse(BaseModel):
    id: UUID
    target_user_id: UUID
    university_id: UUID
    share_reason: str
    shared_at: datetime
    consent_audit_log_id: UUID | None
