from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import InterviewPracticeMode, InterviewResponse, InterviewSession, InterviewSessionStatus
from app.schemas.interviews import InterviewAnswerRequest
from app.services.interview import InterviewSessionService

pytestmark = pytest.mark.asyncio


class FakeSession:
    def __init__(self):
        self.added = []
        self.session_ref: InterviewSession | None = None

    async def execute(self, _query):
        raise AssertionError("execute should not be called in this unit path")

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


async def test_interview_service_start_session_creates_in_progress_session():
    session = FakeSession()
    service = InterviewSessionService(session)

    result = await service.start_session(uuid4())

    assert result.status == "in_progress"
    assert result.total_questions == 3
    assert result.current_question is not None
    assert result.current_question.question_index == 1
    assert len(session.added) == 1


async def test_interview_service_submit_answer_generates_feedback_and_completes_session():
    session = FakeSession()
    service = InterviewSessionService(session)
    interview_session = InterviewSession(
        user_id=uuid4(),
        practice_mode=InterviewPracticeMode.GENERAL,
        status=InterviewSessionStatus.IN_PROGRESS,
        current_question_index=0,
        total_questions=1,
        question_set=["Why are you a strong fit for this scholarship?"],
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

    result = await service.submit_answer(
        user_id=uuid4(),
        session_id=uuid4(),
        payload=InterviewAnswerRequest(
            answer_text=(
                "I am a strong fit because I led a capstone project, worked with real data, "
                "and learned how to connect technical work to community impact. That mix of "
                "evidence, reflection, and clear future goals is exactly what I would bring "
                "to a scholarship-funded graduate program."
            )
        ),
    )

    assert result.status == "completed"
    assert result.latest_feedback is not None
    assert result.latest_feedback.scoring_mode == "rules_fallback"
    assert result.latest_feedback.dimensions
    assert result.responses


def test_interview_answer_request_rejects_too_short_input():
    with pytest.raises(ValidationError):
        InterviewAnswerRequest(answer_text="Too short for useful interview coaching.")
