from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=25)


class RecommendationItem(BaseModel):
    scholarship_id: str
    title: str
    provider_name: str | None
    deadline_at: datetime | None
    estimated_fit_score: float
    fit_band: str
    top_reasons: list[str]
    warnings: list[str]


class RecommendationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RecommendationItem]
