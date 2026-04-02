from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole
from app.schemas.documents import (
    DocumentCitation,
    DocumentDetailResponse,
    DocumentFeedbackResponse,
    DocumentFeedbackRefreshResponse,
    DocumentGeneratedGuidanceItem,
    DocumentGroundedContextSections,
    DocumentQualityGate,
    DocumentQualityMetrics,
    DocumentQualityThresholds,
    DocumentRetrievedGuidanceSnippet,
    DocumentSubmissionResponse,
    DocumentValidatedFact,
)
from app.services.documents.service import DocumentService


class _DummyCurrentUser:
    def __init__(self):
        self.id = uuid4()
        self.role = UserRole.STUDENT
        self._token_capabilities = {
            "document.self.create",
            "document.self.read",
            "document.self.feedback",
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


def _build_document_detail(
    *,
    document_id: str,
    content_text: str,
    scholarship_ids: list[str] | None,
) -> DocumentDetailResponse:
    now = datetime.now(timezone.utc)
    validated_facts = [
        DocumentValidatedFact(
            scholarship_id=scholarship_ids[0] if scholarship_ids else str(uuid4()),
            scholarship_title="Ontario Graduate Scholarship",
            label="Provider",
            value="Ontario Ministry",
            source_url="https://example.test/ogs",
        )
    ]
    guidance = [
        DocumentRetrievedGuidanceSnippet(
            key="sop-structure",
            topic="SOP structure",
            snippet="Use opening, evidence, and impact sections.",
            applies_to="sop",
        )
    ]
    generated = [
        DocumentGeneratedGuidanceItem(
            type="scholarship_fit",
            guidance="Connect your capstone outcomes to this scholarship's impact criteria.",
        )
    ]
    sections = DocumentGroundedContextSections(
        validated_facts=validated_facts,
        retrieved_writing_guidance=guidance,
        generated_guidance=generated,
        limitations=[
            "Generated guidance is advisory and bounded by validated scholarship records.",
        ],
    )
    quality_thresholds = DocumentQualityThresholds(
        min_citation_coverage_ratio=0.8,
        max_caution_note_count=1,
        min_retrieved_guidance_count=1,
        min_generated_guidance_count=1,
    )
    quality_metrics = DocumentQualityMetrics(
        citation_coverage_ratio=1.0,
        validated_fact_count=1,
        retrieved_guidance_count=1,
        generated_guidance_count=1,
        caution_note_count=0,
        review_flag=False,
    )
    quality_gate = DocumentQualityGate(
        thresholds=quality_thresholds,
        policy_version="document.quality.v1",
        citation_coverage_pass=True,
        caution_note_count_pass=True,
        retrieved_guidance_pass=True,
        generated_guidance_pass=True,
        all_passed=True,
    )
    feedback = DocumentFeedbackResponse(
        id=str(uuid4()),
        status="completed",
        summary="Grounded guidance generated successfully.",
        strengths=["Clear narrative arc"],
        revision_priorities=["Add one quantified project outcome"],
        caution_notes=[],
        citations=[
            DocumentCitation(
                source_id="validated-facts",
                title="Validated scholarship facts",
                url_or_ref="grounded_context_sections.validated_facts",
                snippet="Derived from published scholarship data",
                relevance_score=0.88,
            )
        ],
        grounding_score=0.91,
        coverage_flags={
            "motivation": True,
            "preparation": True,
            "future_impact": True,
            "scholarship_fit": True,
        },
        ungrounded_warnings=[],
        grounded_context=[
            "Validated fact: Ontario Graduate Scholarship | Provider = Ontario Ministry"
        ],
        validated_facts=validated_facts,
        retrieved_writing_guidance=guidance,
        generated_guidance=generated,
        limitations=sections.limitations,
        grounded_context_sections=sections,
        quality_metrics=quality_metrics,
        quality_gate=quality_gate,
        limitation_notice="Guidance uses validated scholarship records and bounded retrieval.",
        completed_at=now,
    )
    return DocumentDetailResponse(
        id=document_id,
        title="Grounded SOP Draft",
        document_type="sop",
        input_method="text",
        processing_status="completed",
        original_filename=None,
        created_at=now,
        updated_at=now,
        latest_feedback_at=now,
        scholarship_id=scholarship_ids[0] if scholarship_ids else None,
        scholarship_ids=scholarship_ids,
        content_text=content_text,
        latest_feedback=feedback,
    )


def test_document_feedback_flow_supports_grounded_ids_and_contract(app, client):
    current_user = _DummyCurrentUser()
    db = _NoOpDB()
    scholarship_one = str(uuid4())
    document_id = str(uuid4())
    content_text = (
        "I led a capstone project with measurable outcomes and want to align my graduate "
        "study goals with this scholarship's research and community impact criteria."
    )

    async def override_current_user():
        return current_user

    async def override_db():
        yield db

    async def fake_submit_document(
        self,
        user_id,
        document_type,
        title,
        content_text=None,
        upload=None,
        scholarship_id=None,
        scholarship_ids=None,
    ):
        assert str(user_id) == str(current_user.id)
        assert document_type == "sop"
        assert upload is None
        assert scholarship_id == scholarship_one
        assert scholarship_ids in (None, [])
        return _build_document_detail(
            document_id=document_id,
            content_text=content_text or "",
            scholarship_ids=[scholarship_one],
        )

    async def fake_regenerate_feedback(self, user_id, doc_id):
        assert str(user_id) == str(current_user.id)
        assert str(doc_id) == document_id
        return _build_document_detail(
            document_id=document_id,
            content_text=content_text,
            scholarship_ids=[scholarship_one],
        )

    original_submit = DocumentService.submit_document
    original_regenerate = DocumentService.regenerate_feedback
    DocumentService.submit_document = fake_submit_document  # type: ignore[assignment]
    DocumentService.regenerate_feedback = fake_regenerate_feedback  # type: ignore[assignment]

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    try:
        create_response = client.post(
            "/api/v1/documents",
            data={
                "document_type": "sop",
                "title": "Grounded SOP Draft",
                "content_text": content_text,
                "scholarship_id": scholarship_one,
            },
            headers={"Authorization": "Bearer fake"},
        )
        assert create_response.status_code == 201
        create_payload = DocumentSubmissionResponse.model_validate(create_response.json())
        assert create_payload.document.id == document_id
        assert create_payload.document.latest_feedback is not None
        assert create_payload.document.latest_feedback.citations
        assert "validated scholarship records" in (
            create_payload.document.latest_feedback.limitation_notice.lower()
        )
        assert (
            create_payload.document.latest_feedback.grounded_context_sections.validated_facts
        )

        refresh_response = client.post(
            f"/api/v1/documents/{document_id}/feedback",
            headers={"Authorization": "Bearer fake"},
        )
        assert refresh_response.status_code == 200
        refresh_payload = DocumentFeedbackRefreshResponse.model_validate(refresh_response.json())
        assert refresh_payload.document.latest_feedback is not None
        assert refresh_payload.document.latest_feedback.quality_gate.policy_version == "document.quality.v1"
    finally:
        app.dependency_overrides.clear()
        DocumentService.submit_document = original_submit
        DocumentService.regenerate_feedback = original_regenerate


def test_document_feedback_flow_rejects_invalid_grounding_cleanly(app, client):
    current_user = _DummyCurrentUser()
    db = _NoOpDB()

    async def override_current_user():
        return current_user

    async def override_db():
        yield db

    async def fake_submit_document(
        self,
        user_id,
        document_type,
        title,
        content_text=None,
        upload=None,
        scholarship_id=None,
        scholarship_ids=None,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Scholarship grounding IDs were not found: {scholarship_id}",
        )

    original_submit = DocumentService.submit_document
    DocumentService.submit_document = fake_submit_document  # type: ignore[assignment]
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    try:
        response = client.post(
            "/api/v1/documents",
            data={
                "document_type": "sop",
                "title": "Invalid grounding draft",
                "content_text": (
                    "This draft is long enough to pass minimum validation but references an "
                    "invalid scholarship grounding identifier for testing."
                ),
                "scholarship_id": str(uuid4()),
            },
            headers={"Authorization": "Bearer fake"},
        )
        assert response.status_code == 400
        payload = response.json()
        assert payload["error"]["code"] == "BAD_REQUEST"
        assert "not found" in payload["error"]["message"].lower()
    finally:
        app.dependency_overrides.clear()
        DocumentService.submit_document = original_submit
