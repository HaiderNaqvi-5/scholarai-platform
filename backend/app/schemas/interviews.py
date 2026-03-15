from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InterviewSessionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    practice_mode: str = "general"


class InterviewCurrentQuestionResponse(BaseModel):
    session_id: str
    status: str
    practice_mode: str
    question_index: int
    total_questions: int
    question_text: str | None


class InterviewAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_text: str = Field(min_length=50, max_length=4000)

    @field_validator("answer_text")
    @classmethod
    def validate_answer_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 50:
            raise ValueError("Interview answers must contain at least 50 characters")
        return normalized


class InterviewRubricDimension(BaseModel):
    dimension: str
    score: int
    band: str
    rationale: str


class InterviewAnswerFeedback(BaseModel):
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
    session_id: str
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
