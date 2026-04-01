from datetime import datetime, timezone
from uuid import uuid4

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole
from app.services.documents.service import DocumentService
from app.services.interview.service import InterviewSessionService


class _DummyCurrentUser:
    def __init__(self):
        self.id = uuid4()
        self.role = UserRole.ADMIN
        self._token_capabilities = {
            "document.self.create",
            "document.self.read",
            "document.self.feedback",
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


def test_document_feedback_response_includes_policy_version(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    async def fake_submit_document(self, user_id, document_type, title, content_text=None, upload=None, scholarship_id=None, scholarship_ids=None):
        from app.schemas.documents import (
            DocumentDetailResponse,
            DocumentFeedbackResponse,
            DocumentGroundedContextSections,
            DocumentQualityGate,
            DocumentQualityMetrics,
            DocumentQualityThresholds,
        )

        now = datetime.now(timezone.utc)
        thresholds = DocumentQualityThresholds(
            min_citation_coverage_ratio=0.8,
            max_caution_note_count=1,
            min_retrieved_guidance_count=1,
            min_generated_guidance_count=1,
        )
        quality_gate = DocumentQualityGate(
            thresholds=thresholds,
            policy_version="document.quality.v1",
            citation_coverage_pass=True,
            caution_note_count_pass=True,
            retrieved_guidance_pass=True,
            generated_guidance_pass=True,
            all_passed=True,
        )
        quality_metrics = DocumentQualityMetrics(
            citation_coverage_ratio=1.0,
            validated_fact_count=1,
            retrieved_guidance_count=1,
            generated_guidance_count=1,
            caution_note_count=0,
            review_flag=False,
        )
        feedback = DocumentFeedbackResponse(
            id=str(uuid4()),
            status="completed",
            summary="ok",
            strengths=["s"],
            revision_priorities=["r"],
            caution_notes=[],
            citations=[
                {
                    "source_id": "scholarship:1",
                    "title": "Scholarship record",
                    "url_or_ref": "https://example.test/scholarship",
                    "snippet": "Validated scholarship snippet",
                    "relevance_score": 0.9,
                }
            ],
            grounding_score=0.91,
            coverage_flags={
                "motivation": True,
                "preparation": True,
                "future_impact": True,
                "scholarship_fit": True,
            },
            ungrounded_warnings=[],
            grounded_context=[],
            validated_facts=[],
            retrieved_writing_guidance=[],
            generated_guidance=[],
            limitations=[],
            grounded_context_sections=DocumentGroundedContextSections(
                validated_facts=[],
                retrieved_writing_guidance=[],
                generated_guidance=[],
                limitations=[],
            ),
            quality_metrics=quality_metrics,
            quality_gate=quality_gate,
            limitation_notice="notice",
            completed_at=now,
        )
        return DocumentDetailResponse(
            id=str(uuid4()),
            title=title or "doc",
            document_type=document_type,
            input_method="text",
            processing_status="completed",
            original_filename=None,
            created_at=now,
            updated_at=now,
            latest_feedback_at=now,
            scholarship_id=None,
            scholarship_ids=None,
            content_text=content_text or "",
            latest_feedback=feedback,
        )

    original_submit = DocumentService.submit_document
    DocumentService.submit_document = fake_submit_document  # type: ignore[assignment]

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.post(
        "/api/v1/documents",
        data={
            "document_type": "sop",
            "title": "Doc",
            "content_text": "This is a sufficiently long document text for testing policy version output.",
        },
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()
    DocumentService.submit_document = original_submit

    assert response.status_code == 201
    payload = response.json()
    assert payload["document"]["latest_feedback"]["quality_gate"]["policy_version"] == "document.quality.v1"
    citations = payload["document"]["latest_feedback"]["citations"]
    assert isinstance(citations, list)
    assert citations
    citation = citations[0]
    assert set(citation.keys()) == {
        "source_id",
        "title",
        "url_or_ref",
        "snippet",
        "relevance_score",
    }


def test_interview_summary_response_includes_policy_version(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    async def fake_start_session(self, user_id, practice_mode="general", scholarship_id=None):
        from app.schemas.interviews import (
            InterviewCurrentQuestionResponse,
            InterviewHistorySummary,
            InterviewProgressionGate,
            InterviewProgressionMetrics,
            InterviewProgressionThresholds,
            InterviewSessionSummaryResponse,
            InterviewTrendSummary,
        )

        now = datetime.now(timezone.utc)
        return InterviewSessionSummaryResponse(
            session_id=str(uuid4()),
            scholarship_id=None,
            status="in_progress",
            practice_mode=practice_mode,
            current_question_index=0,
            total_questions=1,
            current_question=InterviewCurrentQuestionResponse(
                session_id=str(uuid4()),
                status="in_progress",
                practice_mode=practice_mode,
                question_index=1,
                total_questions=1,
                question_text="Question?",
            ),
            responses=[],
            latest_feedback=None,
            history_summary=InterviewHistorySummary(answered_count=0, recent_answers=[]),
            trend_summary=InterviewTrendSummary(
                average_score=None,
                score_delta=None,
                score_direction="stable",
                weakest_dimension_overall=None,
                latest_weakest_dimension=None,
                dimension_averages={},
            ),
            progression_metrics=InterviewProgressionMetrics(
                answered_count=0,
                average_score=None,
                first_score=None,
                latest_score=None,
                score_delta=None,
                improvement_ratio=0.0,
                needs_focus_ratio=0.0,
            ),
            progression_gate=InterviewProgressionGate(
                thresholds=InterviewProgressionThresholds(
                    min_answered_count=2,
                    min_average_score=3.0,
                    min_score_delta=0.0,
                    max_needs_focus_ratio=0.5,
                ),
                policy_version="interview.progression.v1",
                answered_count_pass=False,
                average_score_pass=False,
                score_delta_pass=False,
                needs_focus_ratio_pass=True,
                all_passed=False,
            ),
            started_at=now,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )

    original_start = InterviewSessionService.start_session
    InterviewSessionService.start_session = fake_start_session  # type: ignore[assignment]

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.post(
        "/api/v1/interviews",
        json={"practice_mode": "general"},
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()
    InterviewSessionService.start_session = original_start

    assert response.status_code == 201
    payload = response.json()
    assert payload["progression_gate"]["policy_version"] == "interview.progression.v1"


def test_interview_coaching_analytics_response_contract(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    async def fake_get_coaching_analytics(self, user_id):
        from app.schemas.interviews import (
            InterviewCoachingAnalyticsResponse,
            InterviewCoachingRecentSession,
        )

        now = datetime.now(timezone.utc)
        return InterviewCoachingAnalyticsResponse(
            session_count=2,
            answered_count_total=5,
            average_score_overall=3.1,
            score_delta_from_first_session=0.6,
            weakest_dimension_overall="specificity",
            recommended_focuses=[
                "Add one concrete example with measurable impact in each answer.",
            ],
            recent_sessions=[
                InterviewCoachingRecentSession(
                    session_id=str(uuid4()),
                    practice_mode="general",
                    answered_count=3,
                    average_score=3.2,
                    score_delta=0.4,
                    score_direction="improving",
                    weakest_dimension_overall="specificity",
                    completed_at=now,
                    updated_at=now,
                )
            ],
        )

    original_method = InterviewSessionService.get_coaching_analytics
    InterviewSessionService.get_coaching_analytics = fake_get_coaching_analytics  # type: ignore[assignment]

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/api/v1/interviews/coaching-analytics",
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()
    InterviewSessionService.get_coaching_analytics = original_method

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_count"] == 2
    assert payload["answered_count_total"] == 5
    assert payload["average_score_overall"] == 3.1
    assert payload["score_delta_from_first_session"] == 0.6
    assert payload["weakest_dimension_overall"] == "specificity"
    assert isinstance(payload["recommended_focuses"], list)
    assert payload["recent_sessions"]
