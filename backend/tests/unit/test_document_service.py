from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.models import DocumentType, RecordState, Scholarship
from app.services.documents import DocumentService
from app.services.documents.grounding import retrieve_bounded_writing_guidance
from app.services.documents import service as document_service_module

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
        self._scholarships = scholarships or {}

    async def execute(self, query):
        query_text = str(query)
        if "FROM scholarships" in query_text:
            return FakeResult(list(self._scholarships.values()))
        raise AssertionError("unexpected query in unit path")

    def add(self, value):
        if getattr(value, "id", None) is None:
            value.id = uuid4()
        if getattr(value, "created_at", None) is None:
            value.created_at = datetime.now(timezone.utc)
        if getattr(value, "updated_at", None) is None:
            value.updated_at = datetime.now(timezone.utc)
        self.added.append(value)

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
        record_state=RecordState.PUBLISHED,
    )
    scholarship.id = uuid4()
    return scholarship


async def test_document_service_submit_text_generates_feedback():
    session = FakeSession()
    service = DocumentService(session)

    async def fake_load_document(user_id, document_id):
        document = session.added[0]
        feedback = session.added[1]
        document.feedback_entries = [feedback]
        document.id = document_id
        document.user_id = user_id
        return document

    service._load_document = fake_load_document  # type: ignore[method-assign]

    result = await service.submit_document(
        user_id=uuid4(),
        document_type="sop",
        title="Graduate SOP",
        content_text=(
            "I want to pursue graduate study in data science because my research "
            "projects and community work showed me how applied analytics can "
            "improve public services. I led a capstone project, learned from it, "
            "and now want a program that deepens both technical depth and impact."
        ),
    )

    assert result.processing_status == "completed"
    assert result.latest_feedback is not None
    assert result.latest_feedback.status == "completed"
    assert "validated scholarship records" in result.latest_feedback.limitation_notice
    assert len(session.added) == 3
    snapshot = session.added[2]
    assert snapshot.policy_version == "document.quality.v1"


async def test_document_service_rejects_unsupported_file_types():
    session = FakeSession()
    service = DocumentService(session)

    upload = UploadFile(
        file=BytesIO(b"Not a valid document format"),
        filename="draft.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )

    with pytest.raises(HTTPException) as caught:
        await service.submit_document(
            user_id=uuid4(),
            document_type=DocumentType.ESSAY.value,
            title="Essay upload",
            upload=upload,
        )

    assert caught.value.status_code == 400
    assert "plain-text" in str(caught.value.detail)


async def test_grounded_feedback_uses_validated_scholarship_facts_and_sections():
    scholarship = _published_ca_scholarship()
    session = FakeSession({scholarship.id: scholarship})
    service = DocumentService(session)

    async def fake_load_document(user_id, document_id):
        document = session.added[0]
        feedback = session.added[1]
        document.feedback_entries = [feedback]
        document.id = document_id
        document.user_id = user_id
        return document

    service._load_document = fake_load_document  # type: ignore[method-assign]

    result = await service.submit_document(
        user_id=uuid4(),
        document_type="sop",
        title="Grounded SOP",
        content_text=(
            "I want to pursue graduate study in data science and build public-impact "
            "analytics systems. I led a capstone with measurable outcomes and want to "
            "connect this preparation with graduate research and community contribution."
        ),
        scholarship_id=str(scholarship.id),
    )

    feedback = result.latest_feedback
    assert feedback is not None
    assert feedback.validated_facts
    assert all(fact.scholarship_id == str(scholarship.id) for fact in feedback.validated_facts)
    assert feedback.retrieved_writing_guidance
    assert feedback.generated_guidance
    assert feedback.limitations
    assert feedback.grounded_context_sections.validated_facts
    assert feedback.grounded_context_sections.generated_guidance
    assert feedback.quality_metrics.validated_fact_count == len(feedback.validated_facts)
    assert feedback.quality_metrics.citation_coverage_ratio > 0
    assert isinstance(feedback.quality_metrics.review_flag, bool)
    assert feedback.quality_gate.policy_version == "document.quality.v1"
    assert feedback.quality_gate.thresholds.min_citation_coverage_ratio == 0.8
    assert feedback.quality_gate.retrieved_guidance_pass is True
    assert feedback.quality_gate.generated_guidance_pass is True
    assert isinstance(feedback.quality_gate.all_passed, bool)


async def test_invalid_scholarship_grounding_id_fails_cleanly():
    session = FakeSession()
    service = DocumentService(session)

    with pytest.raises(HTTPException) as caught:
        await service.submit_document(
            user_id=uuid4(),
            document_type="sop",
            title="Invalid grounding",
            content_text=(
                "I want to pursue graduate study in data science and build public-impact "
                "analytics systems with measurable outcomes for my community."
            ),
            scholarship_id=str(uuid4()),
        )

    assert caught.value.status_code == 400
    assert "not found" in str(caught.value.detail).lower()


async def test_weak_grounding_fallback_emits_required_contract_fields(monkeypatch):
    scholarship = _published_ca_scholarship()
    session = FakeSession({scholarship.id: scholarship})
    service = DocumentService(session)

    async def fake_load_document(user_id, document_id):
        document = session.added[0]
        feedback = session.added[1]
        document.feedback_entries = [feedback]
        document.id = document_id
        document.user_id = user_id
        return document

    service._load_document = fake_load_document  # type: ignore[method-assign]

    # Force low-confidence grounding deterministically without changing production thresholds.
    monkeypatch.setattr(document_service_module, "build_validated_facts", lambda _scholarships: [])
    monkeypatch.setattr(
        document_service_module,
        "retrieve_bounded_writing_guidance",
        lambda _document_type, _scholarships: [],
    )

    result = await service.submit_document(
        user_id=uuid4(),
        document_type="sop",
        title="Weak Grounding SOP",
        content_text=(
            "This draft is intentionally generic and does not include concrete evidence "
            "or scholarship-specific alignment."
        ),
        scholarship_id=str(scholarship.id),
    )

    feedback = result.latest_feedback
    assert feedback is not None
    assert feedback.grounding_score < 0.5
    assert isinstance(feedback.coverage_flags, dict)
    assert feedback.coverage_flags
    assert feedback.ungrounded_warnings
    assert feedback.citations
    citation = feedback.citations[0]
    assert citation.source_id
    assert citation.title
    assert citation.url_or_ref
    assert citation.snippet
    assert 0.0 <= citation.relevance_score <= 1.0


async def test_quality_metrics_supports_structured_and_legacy_citations():
    service = DocumentService(FakeSession())
    sections = {
        "validated_facts": [
            {"label": "Provider", "value": "A"},
            {"label": "Country", "value": "B"},
        ],
        "retrieved_writing_guidance": [],
        "generated_guidance": [],
    }

    structured_payload = {
        "citations": [
            {
                "source_id": "s1",
                "title": "Source 1",
                "url_or_ref": "https://example.test/1",
                "snippet": "Snippet 1",
                "relevance_score": 0.9,
            }
        ],
        "caution_notes": [],
    }
    structured_metrics = service._build_quality_metrics(structured_payload, sections)
    assert structured_metrics.citation_coverage_ratio == 0.5

    legacy_payload = {
        "citations": ["Source Alpha | legacy_ref", "Source Beta"],
        "caution_notes": [],
    }
    normalized_legacy = service._normalize_citations(legacy_payload["citations"])
    assert len(normalized_legacy) == 2
    assert all(citation.source_id for citation in normalized_legacy)
    assert all(citation.title for citation in normalized_legacy)

    legacy_metrics = service._build_quality_metrics(legacy_payload, sections)
    assert legacy_metrics.citation_coverage_ratio == 1.0


def test_retrieve_bounded_guidance_expands_degree_and_field_dimensions():
    scholarship = _published_ca_scholarship()
    scholarship.category = "stem"
    guidance = retrieve_bounded_writing_guidance("sop", [scholarship])
    keys = {item["key"] for item in guidance}

    assert "general-evidence" in keys
    assert "sop-structure" in keys
    assert "stem-rigor" in keys
    assert "canada-fit" in keys
    assert "degree-ms-research-readiness" in keys
    assert "field-data-science-method" in keys
    assert "field-analytics-impact" in keys


async def test_grounded_feedback_citations_include_guidance_context_references():
    scholarship = _published_ca_scholarship()
    scholarship.category = "stem"
    session = FakeSession({scholarship.id: scholarship})
    service = DocumentService(session)

    async def fake_load_document(user_id, document_id):
        document = session.added[0]
        feedback = session.added[1]
        document.feedback_entries = [feedback]
        document.id = document_id
        document.user_id = user_id
        return document

    service._load_document = fake_load_document  # type: ignore[method-assign]

    result = await service.submit_document(
        user_id=uuid4(),
        document_type="sop",
        title="Guidance-Cited SOP",
        content_text=(
            "I want to pursue graduate study in data science and build public-impact analytics systems. "
            "My capstone modeled service demand and informed resource planning decisions."
        ),
        scholarship_id=str(scholarship.id),
    )

    feedback = result.latest_feedback
    assert feedback is not None
    assert any(c.source_id.startswith("guidance:") for c in feedback.citations)
    assert any(c.source_id == "validated-facts" for c in feedback.citations)
