"""Schemas for the Pakistan-context SOP builder (Feature 7, PRD §7)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SOPInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    academic_background: str = Field(min_length=20, max_length=2000)
    research_experience: str | None = Field(default=None, max_length=2000)
    professional_experience: str | None = Field(default=None, max_length=2000)
    why_this_program: str = Field(min_length=10, max_length=2000)
    why_this_country: str | None = Field(default=None, max_length=1500)
    career_goals: str = Field(min_length=10, max_length=2000)
    challenges_overcome: str | None = Field(default=None, max_length=1500)
    gap_explanation: str | None = Field(default=None, max_length=1500)


class SOPDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scholarship_id: UUID | None = None
    university_id: UUID | None = None
    program_name: str | None = Field(default=None, max_length=255)
    sop_inputs: SOPInputs


class SOPParagraphFeedback(BaseModel):
    index: int
    paragraph_label: str
    strength: str
    weakness: str
    suggestion: str


class SOPGroundedContext(BaseModel):
    validated_scholarship_facts: list[str] = Field(default_factory=list)
    retrieved_writing_guidance: list[str] = Field(default_factory=list)
    generated_guidance: str | None = None
    limitations: str


class SOPDraftResponse(BaseModel):
    document_id: UUID
    document_type: str = "sop"
    draft_content: str
    word_count: int
    paragraph_labels: list[str]
    grounded_context: SOPGroundedContext
    line_feedback: list[SOPParagraphFeedback] | None = None
    model_used: str
    used_llm: bool
    created_at: datetime
