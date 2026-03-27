from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import InterviewPracticeMode


class InterviewSessionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    practice_mode: str = "general"
    scholarship_id: str | None = None

    @model_validator(mode="after")
    def validate_practice_mode(self) -> "InterviewSessionStartRequest":
        default_mode = InterviewPracticeMode.GENERAL.value
        normalized_mode = (self.practice_mode or default_mode).strip().lower()
        allowed_modes = {member.value for member in InterviewPracticeMode}
        if normalized_mode not in allowed_modes:
            options = "' or '".join(sorted(allowed_modes))
            raise ValueError(f"practice_mode must be '{options}'")
        self.practice_mode = normalized_mode
        return self


class InterviewCurrentQuestionResponse(BaseModel):
    session_id: str
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
    targeted_follow_up_actions: list[str] = Field(default_factory=list)
    rubric_focus_dimension: str | None = None
    dimensions: list[InterviewRubricDimension]
    limitation_notice: str
    created_at: datetime | None = None


class InterviewHistorySummaryItem(BaseModel):
    question_index: int
    question_text: str
    overall_score: float
    weakest_dimension: str | None
    strongest_dimension: str | None
    improvement_focus: str | None


class InterviewHistorySummary(BaseModel):
    answered_count: int
    recent_answers: list[InterviewHistorySummaryItem]


class InterviewTrendSummary(BaseModel):
    average_score: float | None
    score_delta: float | None
    score_direction: str
    weakest_dimension_overall: str | None
    latest_weakest_dimension: str | None
    dimension_averages: dict[str, float]


class InterviewProgressionMetrics(BaseModel):
    answered_count: int = Field(ge=0)
    average_score: float | None = None
    first_score: float | None = None
    latest_score: float | None = None
    score_delta: float | None = None
    improvement_ratio: float = Field(ge=0.0, le=1.0)
    needs_focus_ratio: float = Field(ge=0.0, le=1.0)
    follow_up_actionability_ratio: float = Field(ge=0.0, le=1.0)
    adaptive_guidance_coverage: float = Field(ge=0.0, le=1.0)


class InterviewProgressionThresholds(BaseModel):
    min_answered_count: int = Field(ge=0)
    min_average_score: float
    min_score_delta: float
    max_needs_focus_ratio: float = Field(ge=0.0, le=1.0)
    min_follow_up_actionability_ratio: float = Field(ge=0.0, le=1.0)
    min_adaptive_guidance_coverage: float = Field(ge=0.0, le=1.0)


class InterviewProgressionGate(BaseModel):
    thresholds: InterviewProgressionThresholds
    policy_version: str
    answered_count_pass: bool
    average_score_pass: bool
    score_delta_pass: bool
    needs_focus_ratio_pass: bool
    follow_up_actionability_pass: bool
    adaptive_guidance_pass: bool
    all_passed: bool


class InterviewSessionSummaryResponse(BaseModel):
    session_id: str
    scholarship_id: str | None = None
    status: str
    practice_mode: str
    current_question_index: int
    total_questions: int
    current_question: InterviewCurrentQuestionResponse | None
    responses: list[InterviewAnswerFeedback]
    latest_feedback: InterviewAnswerFeedback | None
    history_summary: InterviewHistorySummary
    trend_summary: InterviewTrendSummary
    progression_metrics: InterviewProgressionMetrics
    progression_gate: InterviewProgressionGate
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
