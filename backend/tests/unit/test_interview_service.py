from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models import (
    InterviewPracticeMode,
    InterviewResponse,
    InterviewSession,
    InterviewSessionStatus,
    RecordState,
    Scholarship,
)
from app.schemas.interviews import InterviewAnswerFeedback, InterviewAnswerRequest, InterviewRubricDimension
from app.services.interview import InterviewSessionService

pytestmark = pytest.mark.asyncio


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class FakeSession:
    def __init__(self, scholarships: dict | None = None):
        self.added = []
        self.session_ref: InterviewSession | None = None
        self._scholarships = scholarships or {}

    async def execute(self, query):
        query_text = str(query)
        if "FROM scholarships" in query_text:
            return FakeResult(list(self._scholarships.values()))
        if "FROM interview_sessions" in query_text:
            return FakeResult([self.session_ref] if self.session_ref else [])
        raise AssertionError("unexpected query in unit path")

    def add(self, value):
        if getattr(value, "id", None) is None:
            value.id = uuid4()
        if getattr(value, "created_at", None) is None:
            value.created_at = datetime.now(timezone.utc)
        if getattr(value, "updated_at", None) is None:
            value.updated_at = datetime.now(timezone.utc)
        self.added.append(value)

        if isinstance(value, InterviewSession):
            self.session_ref = value
            if getattr(value, "responses", None) is None:
                value.responses = []
        if isinstance(value, InterviewResponse) and self.session_ref is not None:
            self.session_ref.responses.append(value)

    async def flush(self):
        return None

    async def refresh(self, _value):
        return None


def _published_ca_scholarship() -> Scholarship:
    scholarship = Scholarship(
        title="Ontario Graduate Scholarship",
        provider_name="Ontario Ministry of Colleges and Universities",
        country_code="CA",
        summary="Graduate scholarship for high-achieving students in Ontario.",
        funding_summary="Annual scholarship funding for graduate study.",
        source_url="https://example.org/ogs",
        field_tags=["data science", "analytics"],
        degree_levels=["MS"],
        citizenship_rules=["PK", "CA"],
        category="research",
        record_state=RecordState.PUBLISHED,
    )
    scholarship.id = uuid4()
    return scholarship


def _feedback(
    *,
    question_index: int,
    question_text: str,
    answer_text: str,
    overall_score: float,
    dimensions: list[tuple[str, int]],
) -> InterviewAnswerFeedback:
    return InterviewAnswerFeedback(
        question_index=question_index,
        question_text=question_text,
        answer_text=answer_text,
        overall_score=overall_score,
        overall_band="solid",
        scoring_mode="rules_fallback",
        summary_feedback="Structured practice feedback.",
        strengths=["Structured answer."],
        improvement_prompts=["Add a concrete measurable outcome."],
        dimensions=[
            InterviewRubricDimension(
                dimension=name,
                score=score,
                band="solid" if score >= 3 else "developing",
                rationale=f"{name} rationale",
            )
            for name, score in dimensions
        ],
        limitation_notice="Practice-only guidance.",
    )


async def test_interview_service_general_vs_scholarship_mode():
    scholarship = _published_ca_scholarship()
    session = FakeSession({scholarship.id: scholarship})
    service = InterviewSessionService(session)

    general_result = await service.start_session(uuid4(), practice_mode="general")
    scholarship_result = await service.start_session(
        uuid4(),
        practice_mode="scholarship",
        scholarship_id=str(scholarship.id),
    )

    assert general_result.practice_mode == "general"
    assert scholarship_result.practice_mode == "scholarship"
    assert scholarship_result.scholarship_id == str(scholarship.id)
    assert general_result.current_question is not None
    assert scholarship_result.current_question is not None
    assert (
        general_result.current_question.question_text
        != scholarship_result.current_question.question_text
    )


async def test_interview_service_adapts_next_prompt_to_weakest_dimension():
    session = FakeSession()
    service = InterviewSessionService(session)
    interview_session = InterviewSession(
        user_id=uuid4(),
        practice_mode=InterviewPracticeMode.GENERAL,
        status=InterviewSessionStatus.IN_PROGRESS,
        current_question_index=0,
        total_questions=2,
        question_set=["Initial question?", "Second question?"],
        started_at=datetime.now(timezone.utc),
    )
    interview_session.id = uuid4()
    interview_session.created_at = datetime.now(timezone.utc)
    interview_session.updated_at = datetime.now(timezone.utc)
    interview_session.responses = []
    session.session_ref = interview_session

    async def fake_load_session(user_id, session_id):
        interview_session.user_id = user_id
        interview_session.id = session_id
        return interview_session

    service._load_session = fake_load_session  # type: ignore[method-assign]
    service.scoring_service.score_answer = lambda question_index, question_text, answer_text: _feedback(  # type: ignore[method-assign]
        question_index=question_index,
        question_text=question_text,
        answer_text=answer_text,
        overall_score=3.0,
        dimensions=[
            ("clarity", 4),
            ("relevance", 4),
            ("confidence", 4),
            ("specificity", 1),
        ],
    )

    result = await service.submit_answer(
        user_id=uuid4(),
        session_id=uuid4(),
        payload=InterviewAnswerRequest(
            answer_text=(
                "I led a project and I am ready to contribute. I built data pipelines "
                "and learned from the process with clear ownership and confidence."
            )
        ),
    )

    assert result.current_question is not None
    assert "Use one concrete example" in (result.current_question.question_text or "")
    assert "Use one concrete example" in interview_session.question_set[1]


async def test_interview_service_session_history_and_trend_summary():
    session = FakeSession()
    service = InterviewSessionService(session)
    interview_session = InterviewSession(
        user_id=uuid4(),
        practice_mode=InterviewPracticeMode.GENERAL,
        status=InterviewSessionStatus.IN_PROGRESS,
        current_question_index=0,
        total_questions=2,
        question_set=["Question one?", "Question two?"],
        started_at=datetime.now(timezone.utc),
    )
    interview_session.id = uuid4()
    interview_session.created_at = datetime.now(timezone.utc)
    interview_session.updated_at = datetime.now(timezone.utc)
    interview_session.responses = []
    session.session_ref = interview_session

    async def fake_load_session(user_id, session_id):
        interview_session.user_id = user_id
        interview_session.id = session_id
        return interview_session

    service._load_session = fake_load_session  # type: ignore[method-assign]

    feedback_values = iter(
        [
            _feedback(
                question_index=0,
                question_text="Question one?",
                answer_text="First answer",
                overall_score=2.0,
                dimensions=[("clarity", 2), ("relevance", 1), ("confidence", 2), ("specificity", 2)],
            ),
            _feedback(
                question_index=1,
                question_text="Question two?",
                answer_text="Second answer",
                overall_score=3.5,
                dimensions=[("clarity", 4), ("relevance", 3), ("confidence", 3), ("specificity", 3)],
            ),
        ]
    )
    service.scoring_service.score_answer = lambda question_index, question_text, answer_text: next(feedback_values)  # type: ignore[method-assign]

    await service.submit_answer(
        user_id=uuid4(),
        session_id=uuid4(),
        payload=InterviewAnswerRequest(
            answer_text=(
                "I built a data dashboard and used it to support community planning "
                "decisions under uncertainty."
            )
        ),
    )
    result = await service.submit_answer(
        user_id=uuid4(),
        session_id=uuid4(),
        payload=InterviewAnswerRequest(
            answer_text=(
                "I improved the project by adding measurable outcomes and clearer "
                "communication tied directly to the question."
            )
        ),
    )

    assert result.history_summary.answered_count == 2
    assert len(result.history_summary.recent_answers) == 2
    assert result.trend_summary.average_score == 2.75
    assert result.trend_summary.score_direction == "improving"
    assert result.trend_summary.latest_weakest_dimension in {"relevance", "confidence", "specificity", "clarity"}
    assert result.progression_metrics.answered_count == 2
    assert result.progression_metrics.first_score == 2.0
    assert result.progression_metrics.latest_score == 3.5
    assert result.progression_metrics.score_delta == 1.5
    assert result.progression_metrics.improvement_ratio == 1.0
    assert result.progression_metrics.needs_focus_ratio == 0.5
    assert result.progression_gate.thresholds.min_answered_count == 2
    assert result.progression_gate.answered_count_pass is True
    assert result.progression_gate.average_score_pass is False
    assert result.progression_gate.score_delta_pass is True
    assert result.progression_gate.needs_focus_ratio_pass is True
    assert result.progression_gate.all_passed is False


async def test_interview_invalid_scholarship_grounding_fails_cleanly():
    session = FakeSession()
    service = InterviewSessionService(session)

    with pytest.raises(HTTPException) as caught:
        await service.start_session(
            user_id=uuid4(),
            practice_mode="scholarship",
            scholarship_id=str(uuid4()),
        )

    assert caught.value.status_code == 400
    assert "not found" in str(caught.value.detail).lower()


async def test_interview_answer_request_rejects_too_short_input():
    with pytest.raises(ValidationError):
        InterviewAnswerRequest(answer_text="Too short for useful interview coaching.")
