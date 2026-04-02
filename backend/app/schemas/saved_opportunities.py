from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SavedOpportunityTrackerStatus = Literal["saved", "in_progress", "applied", "closed"]


class SavedOpportunityStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: SavedOpportunityTrackerStatus


class SavedOpportunityItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scholarship_id: str
    title: str
    provider_name: str | None
    country_code: str
    deadline_at: datetime | None
    record_state: str
    saved_at: datetime
    tracker_status: SavedOpportunityTrackerStatus


class SavedOpportunityListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SavedOpportunityItem]
    total: int = Field(ge=0)
