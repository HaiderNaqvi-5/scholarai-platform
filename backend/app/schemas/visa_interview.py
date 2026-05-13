"""Schemas for visa interview simulator (Feature 8, PRD §8)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


_ALLOWED_COUNTRIES = {"GB", "US", "CA", "DE"}
_ALLOWED_PRACTICE_MODES = {"study", "exam"}


class VisaInterviewStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country: str = Field(min_length=2, max_length=2)
    visa_type: str | None = Field(default=None, max_length=32)
    practice_mode: str = Field(default="study")
    scholarship_id: UUID | None = None

    @field_validator("country")
    @classmethod
    def country_supported(cls, value: str) -> str:
        v = value.upper()
        if v not in _ALLOWED_COUNTRIES:
            raise ValueError(
                "country must be one of: " + ", ".join(sorted(_ALLOWED_COUNTRIES))
            )
        return v

    @field_validator("practice_mode")
    @classmethod
    def mode_allowed(cls, value: str) -> str:
        v = value.lower()
        if v not in _ALLOWED_PRACTICE_MODES:
            raise ValueError("practice_mode must be 'study' or 'exam'")
        return v


class VisaInterviewQuestionDTO(BaseModel):
    id: UUID
    country: str
    visa_type: str
    category: str
    question_text: str
    difficulty: str


class VisaInterviewStartResponse(BaseModel):
    session_id: UUID
    country: str
    visa_type: str
    practice_mode: str
    total_questions: int
    first_question: VisaInterviewQuestionDTO | None
    started_at: datetime


class VisaInterviewAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: UUID
    answer_text: str = Field(min_length=1, max_length=4000)


class VisaInterviewRubric(BaseModel):
    clarity_score: int
    confidence_score: int
    relevance_score: int
    overall_score: int
    red_flags: list[str]
    missing_elements: list[str]
    what_was_good: str
    ideal_answer_summary: str
    used_llm: bool


class VisaInterviewProgress(BaseModel):
    answered: int
    total: int


class VisaInterviewAnswerResponse(BaseModel):
    evaluation: VisaInterviewRubric
    next_question: VisaInterviewQuestionDTO | None
    session_progress: VisaInterviewProgress
    partial_summary: dict | None = None


class VisaInterviewSessionSummary(BaseModel):
    session_id: UUID
    country: str
    visa_type: str
    answered: int
    total: int
    average_score: float
    score_breakdown: dict[str, float]
    red_flag_count: int
    areas_to_improve: list[str]
    transcript_document_id: UUID | None = None
