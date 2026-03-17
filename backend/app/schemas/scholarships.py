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


class ScholarshipAppliedFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country_code: str | None = None
    query: str | None = None
    field_tag: str | None = None
    degree_level: str | None = None
    provider: str | None = None
    funding_type: str | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    has_deadline: bool | None = None
    deadline_within_days: int | None = None
    deadline_after: datetime | None = None
    deadline_before: datetime | None = None
    sort: str = "deadline"


class ScholarshipDetailResponse(ScholarshipListItem):
    summary: str | None
    funding_summary: str | None
    funding_type: str | None
    funding_amount_min: float | None
    funding_amount_max: float | None
    source_url: str
    field_tags: list[str]
    degree_levels: list[str]
    citizenship_rules: list[str]
    min_gpa_value: float | None
    source_document_ref: str | None
    requirement_summary: list[str]
    last_validated_at: datetime | None
    published_at: datetime | None
    publication_hint: str


class ScholarshipListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ScholarshipListItem]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=50)
    has_more: bool
    applied_filters: ScholarshipAppliedFilters
