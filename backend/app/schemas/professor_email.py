"""Schemas for the Elite professor cold-email generator (PRD §0.6)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProfessorEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    professor_name: str = Field(min_length=2, max_length=160)
    university: str = Field(min_length=2, max_length=200)
    research_area: str = Field(min_length=3, max_length=400)
    student_pitch: str = Field(
        min_length=20,
        max_length=2000,
        description="The student's background + why they fit this professor's lab.",
    )
    position_type: Literal["phd", "ra"] = Field(
        default="phd",
        description="Drives the email's ask: PhD position vs research assistantship.",
    )


class ProfessorEmailResponse(BaseModel):
    document_id: UUID
    document_type: str = "professor_email"
    email_subject: str
    email_body: str
    word_count: int
    used_llm: bool
    model_used: str
    limitations: str
    created_at: datetime
