from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MentorFeedbackRequest(BaseModel):
    """Payload a mentor submits when reviewing a student document."""
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., min_length=10, max_length=2000)
    strengths: list[str] = Field(default_factory=list)
    revision_priorities: list[str] = Field(default_factory=list)
    caution_notes: list[str] = Field(default_factory=list)


class MentorFeedbackResponse(BaseModel):
    """Response after mentor feedback is persisted."""
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    document_id: UUID
    mentor_id: UUID
    summary: str
    strengths: list[str]
    revision_priorities: list[str]
    caution_notes: list[str]
    submitted_at: datetime | None
