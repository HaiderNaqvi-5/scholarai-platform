from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole
from app.schemas.interviews import InterviewAnswerFeedback, InterviewRubricDimension
from app.services.interview.service import InterviewSessionService


class _DummyCurrentUser:
    def __init__(self):
        self.id = uuid4()
        self.role = UserRole.STUDENT
        self._token_capabilities = {
            "interview.self.create",
            "interview.self.read",
            "interview.self.respond",
        }


class _NoOpDB:
    async def execute(self, _query):
        return None

    def add(self, _value):
        return None

    async def flush(self):
        return None

    async def refresh(self, _value):
        return None


class _FakeInterviewService:
    def __init__(self, _db):
        self._session_id = str(uuid4())
        self._scholarship_id = str(uuid4())
        self._response_count = 0
        self._responses: list[dict] = []
        self._question_set = [
            "Why are you applying for this scholarship now?",
            "Describe one measurable project outcome from your prior work.",
            "How will you use scholarship funding for concrete impact?",
        ]

    async def start_session(self, user_id, practice_mode="general", scholarship_id=None):
        assert practice_mode in {"general", "scholarship"}
        assert str(user_id)
        if practice_mode == "scholarship":
            assert scholarship_id is not None
        return self._build_summary(status="in_progress")

    async def get_session(self, user_id, session_id):
        assert str(user_id)
        assert str(session_id) == self._session_id
        return self._build_summary(
            status="completed" if self._response_count >= len(self._question_set) else "in_progress"
        )

    async def get_current_question(self, user_id, session_id):
        assert str(user_id)
        assert str(session_id) == self._session_id
        index = min(self._response_count, len(self._question_set) - 1)
        return {
            "session_id": self._session_id,
            "status": "completed" if self._response_count >= len(self._question_set) else "in_progress",
            "practice_mode": "scholarship",
            "question_index": index + 1,
            "total_questions": len(self._question_set),
            "question_text": None if self._response_count >= len(self._question_set) else self._question_set[index],
        }

    async def submit_answer(self, user_id, session_id, payload):
        assert str(user_id)
        assert str(session_id) == self._session_id
        self._response_count += 1
        response_item = {
            "question_index": self._response_count - 1,
            "question_text": self._question_set[self._response_count - 1],
            "answer_text": payload.answer_text or "audio-answer",
            "overall_score": 3.1 if self._response_count < 3 else 3.4,
            "overall_band": "solid",
            "scoring_mode": "rules_fallback",
            "summary_feedback": "Structured feedback.",
            "strengths": ["Direct answer"],
            "improvement_prompts": ["Add one measurable result"],
            "dimensions": [
                {"dimension": "clarity", "score": 3, "band": "solid", "rationale": "Clear"},
                {"dimension": "relevance", "score": 3, "band": "solid", "rationale": "Relevant"},
                {"dimension": "confidence", "score": 3, "band": "solid", "rationale": "Confident"},
                {"dimension": "specificity", "score": 2, "band": "developing", "rationale": "Needs numbers"},
            ],
            "limitation_notice": "Practice-only guidance.",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._responses.append(response_item)
        weakest_dimension = min(
            response_item["dimensions"],
            key=lambda item: (item["score"], item["dimension"]),
        )["dimension"]
        strongest_dimension = max(
            response_item["dimensions"],
            key=lambda item: (item["score"], item["dimension"]),
        )["dimension"]
        self._responses[-1]["history_summary_item"] = {
            "question_index": response_item["question_index"],
            "question_text": response_item["question_text"],
            "overall_score": response_item["overall_score"],
            "weakest_dimension": weakest_dimension,
            "strongest_dimension": strongest_dimension,
            "improvement_focus": response_item["improvement_prompts"][0],
        }
        return self._build_summary(
            status="completed" if self._response_count >= len(self._question_set) else "in_progress"
        )

    def _build_summary(self, *, status: str):
        now = datetime.now(timezone.utc)
        latest_feedback = self._responses[-1] if self._responses else None
        average_score = None
        if self._responses:
            average_score = round(
                sum(item["overall_score"] for item in self._responses) / len(self._responses),
                2,
            )
        progression_all_passed = self._response_count >= 2 and (average_score or 0) >= 3.0
        return {
            "session_id": self._session_id,
            "scholarship_id": self._scholarship_id,
            "status": status,
            "practice_mode": "scholarship",
            "current_question_index": min(self._response_count, len(self._question_set)),
            "total_questions": len(self._question_set),
            "current_question": {
                "session_id": self._session_id,
                "status": status,
                "practice_mode": "scholarship",
                "question_index": min(self._response_count + 1, len(self._question_set)),
                "total_questions": len(self._question_set),
                "question_text": None if status == "completed" else self._question_set[self._response_count],
            },
            "responses": self._responses,
            "latest_feedback": latest_feedback,
            "history_summary": {
                "answered_count": self._response_count,
                "recent_answers": [
                    response["history_summary_item"]
                    for response in self._responses[-3:]
                ],
            },
            "trend_summary": {
                "average_score": average_score,
                "score_delta": round(self._responses[-1]["overall_score"] - self._responses[0]["overall_score"], 2)
                if len(self._responses) >= 2
                else None,
                "score_direction": "improving" if len(self._responses) >= 2 else "insufficient_data",
                "weakest_dimension_overall": "specificity",
                "latest_weakest_dimension": "specificity",
                "dimension_averages": {
                    "clarity": 3.0,
                    "relevance": 3.0,
                    "confidence": 3.0,
                    "specificity": 2.0,
                },
            },
            "progression_metrics": {
                "answered_count": self._response_count,
                "average_score": average_score,
                "first_score": self._responses[0]["overall_score"] if self._responses else None,
                "latest_score": self._responses[-1]["overall_score"] if self._responses else None,
                "score_delta": round(self._responses[-1]["overall_score"] - self._responses[0]["overall_score"], 2)
                if len(self._responses) >= 2
                else None,
                "improvement_ratio": 1.0 if len(self._responses) >= 2 else 0.0,
                "needs_focus_ratio": 1.0 if self._response_count == 1 else 0.33 if self._response_count > 1 else 0.0,
            },
            "progression_gate": {
                "thresholds": {
                    "min_answered_count": 2,
                    "min_average_score": 3.0,
                    "min_score_delta": 0.0,
                    "max_needs_focus_ratio": 0.5,
                },
                "policy_version": "interview.progression.v1",
                "answered_count_pass": self._response_count >= 2,
                "average_score_pass": (average_score or 0) >= 3.0,
                "score_delta_pass": True if len(self._responses) >= 2 else False,
                "needs_focus_ratio_pass": True,
                "all_passed": progression_all_passed,
            },
            "started_at": now.isoformat(),
            "completed_at": now.isoformat() if status == "completed" else None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }


def test_interview_session_full_flow_and_coaching_outputs(app, client):
    user = _DummyCurrentUser()
    db = _NoOpDB()
    fake_service = _FakeInterviewService(db)

    async def override_current_user():
        return user

    async def override_db():
        yield db

    original_service = InterviewSessionService
    import app.api.v1.routes.interview as interview_routes

    interview_routes.InterviewSessionService = lambda _db: fake_service  # type: ignore[assignment]
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    try:
        start_response = client.post(
            "/api/v1/interviews",
            json={"practice_mode": "scholarship", "scholarship_id": str(uuid4())},
            headers={"Authorization": "Bearer fake"},
        )
        assert start_response.status_code == 201
        start_payload = start_response.json()
        session_id = start_payload["session_id"]
        UUID(session_id)
        assert start_payload["practice_mode"] == "scholarship"
        assert start_payload["status"] == "in_progress"

        question_response = client.get(
            f"/api/v1/interviews/{session_id}/question",
            headers={"Authorization": "Bearer fake"},
        )
        assert question_response.status_code == 200
        assert question_response.json()["question_text"]

        answer_one = client.post(
            f"/api/v1/interviews/{session_id}/responses",
            json={
                "answer_text": (
                    "I built a demand-forecasting model for university labs and used the results "
                    "to improve scheduling accuracy by 18 percent over one semester."
                )
            },
            headers={"Authorization": "Bearer fake"},
        )
        assert answer_one.status_code == 200
        payload_one = answer_one.json()
        assert payload_one["history_summary"]["answered_count"] == 1
        assert payload_one["latest_feedback"]["summary_feedback"]

        answer_two = client.post(
            f"/api/v1/interviews/{session_id}/responses",
            json={
                "answer_text": (
                    "I translated those model outputs into a resource plan and validated outcomes "
                    "with faculty stakeholders to improve allocation decisions."
                )
            },
            headers={"Authorization": "Bearer fake"},
        )
        assert answer_two.status_code == 200
        payload_two = answer_two.json()
        assert payload_two["progression_gate"]["policy_version"] == "interview.progression.v1"
        assert payload_two["progression_metrics"]["answered_count"] == 2

        answer_three = client.post(
            f"/api/v1/interviews/{session_id}/responses",
            json={
                "answer_text": (
                    "With scholarship funding I would extend this work to community-facing systems "
                    "and publish implementation guidance tied to measurable outcomes."
                )
            },
            headers={"Authorization": "Bearer fake"},
        )
        assert answer_three.status_code == 200
        payload_three = answer_three.json()
        assert payload_three["status"] == "completed"
        assert payload_three["trend_summary"]["average_score"] is not None
        assert payload_three["latest_feedback"]["dimensions"]
        first_dimension = InterviewRubricDimension.model_validate(
            payload_three["latest_feedback"]["dimensions"][0]
        )
        assert first_dimension.dimension in {"clarity", "relevance", "confidence", "specificity"}
        parsed_feedback = InterviewAnswerFeedback.model_validate(payload_three["latest_feedback"])
        assert parsed_feedback.scoring_mode == "rules_fallback"
    finally:
        app.dependency_overrides.clear()
        interview_routes.InterviewSessionService = original_service  # type: ignore[assignment]


def test_interview_routes_require_interview_capabilities(app, client):
    user = _DummyCurrentUser()
    user._token_capabilities = {"profile.self.read"}
    db = _NoOpDB()

    async def override_current_user():
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    session_id = str(uuid4())
    start_response = client.post(
        "/api/v1/interviews",
        json={"practice_mode": "general"},
        headers={"Authorization": "Bearer fake"},
    )
    read_response = client.get(
        f"/api/v1/interviews/{session_id}",
        headers={"Authorization": "Bearer fake"},
    )
    respond_response = client.post(
        f"/api/v1/interviews/{session_id}/responses",
        json={
            "answer_text": (
                "I built a project with measurable outcomes and can explain the impact with "
                "clear evidence tied to the prompt."
            )
        },
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert start_response.status_code == 403
    assert read_response.status_code == 403
    assert respond_response.status_code == 403
    assert start_response.json()["error"]["code"] == "auth_insufficient_permissions"
