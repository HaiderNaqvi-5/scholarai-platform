from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SavedOpportunityItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scholarship_id: str
    title: str
    provider_name: str | None
    country_code: str
    deadline_at: datetime | None
    record_state: str
    saved_at: datetime


class SavedOpportunityListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SavedOpportunityItem]
    total: int = Field(ge=0)
