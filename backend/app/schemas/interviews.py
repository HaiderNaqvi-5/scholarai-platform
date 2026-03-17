from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InterviewSessionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    practice_mode: str = "general"
    scholarship_id: str | None = None


class InterviewCurrentQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    session_id: UUID
    status: str
    practice_mode: str
    question_index: int
    total_questions: int
    question_text: str | None


class InterviewAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_text: str | None = Field(default=None, max_length=4000)
    audio_b64: str | None = Field(default=None)

    @model_validator(mode='after')
    def validate_content(self) -> 'InterviewAnswerRequest':
        if not self.answer_text and not self.audio_b64:
            raise ValueError("Must provide either answer_text or audio_b64")
        if self.answer_text and len(self.answer_text.strip()) < 50:
            raise ValueError("Text answers must contain at least 50 characters")
        if self.answer_text:
            self.answer_text = self.answer_text.strip()
        return self


    rationale: str


class InterviewRubricDimension(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    dimension: str
    score: int
    band: str
    rationale: str


class InterviewAnswerFeedback(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    question_index: int
    question_text: str
    answer_text: str
    overall_score: float
    overall_band: str
    scoring_mode: str
    summary_feedback: str
    strengths: list[str]
    improvement_prompts: list[str]
    dimensions: list[InterviewRubricDimension]
    limitation_notice: str
    created_at: datetime | None = None


class InterviewSessionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    session_id: UUID
    status: str
    practice_mode: str
    current_question_index: int
    total_questions: int
    current_question: InterviewCurrentQuestionResponse | None
    responses: list[InterviewAnswerFeedback]
    latest_feedback: InterviewAnswerFeedback | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
