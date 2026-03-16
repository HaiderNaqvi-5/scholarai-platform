from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScholarshipListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scholarship_id: str
    title: str
    provider_name: str | None
    country_code: str
    deadline_at: datetime | None
    record_state: str


class ScholarshipDetailResponse(ScholarshipListItem):
    summary: str | None
    funding_summary: str | None
    source_url: str
    field_tags: list[str]
    degree_levels: list[str]
    citizenship_rules: list[str]
    min_gpa_value: float | None
    source_document_ref: str | None


class ScholarshipListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ScholarshipListItem]
    total: int = Field(ge=0)
    applied_country_code: str | None = None
