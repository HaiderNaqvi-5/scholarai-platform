from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=25)


class RecommendationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    scholarship_id: str
    title: str
    provider_name: str | None
    country_code: str
    deadline_at: datetime | None
    record_state: str
    estimated_fit_score: float
    fit_band: str
    match_summary: str
    matched_criteria: list[str]
    constraint_notes: list[str]
    top_reasons: list[str]
    warnings: list[str]
    shap_explanation: dict[str, str] | None = None


class RecommendationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RecommendationItem]
    total: int = Field(ge=0)
