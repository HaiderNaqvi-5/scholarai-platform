from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models import RecordState, Scholarship, SourceRegistry, UserRole
from app.schemas.curation import CurationActionRequest, CurationRawImportRequest
from app.services.curation import CurationService

pytestmark = pytest.mark.asyncio


class FakeSession:
    def __init__(self):
        self.added = []

    async def execute(self, _query):
        return FakeResult(None)

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


class FakeResult:
    def __init__(self, item):
        self.item = item

    def scalar_one_or_none(self):
        return self.item


def make_record(state: RecordState) -> Scholarship:
    record = Scholarship(
        title="Scholarship Record",
        provider_name="Provider",
        country_code="CA",
        summary="Curated summary",
        funding_summary="Funding details",
        source_url="https://example.com/scholarship",
        field_tags=["data science"],
        degree_levels=["MS"],
        citizenship_rules=["PK"],
        record_state=state,
    )
    record.id = uuid4()
    record.created_at = datetime.now(timezone.utc)
    record.updated_at = datetime.now(timezone.utc)
    record.source_registry = None
    return record


async def test_curation_service_approve_moves_raw_to_validated():
    session = FakeSession()
    service = CurationService(session)
    record = make_record(RecordState.RAW)

    async def fake_load_record(_record_id, _actor_user):
        return record

    service._load_record = fake_load_record  # type: ignore[method-assign]

    actor_user = type("U", (), {"id": uuid4(), "role": UserRole.ADMIN, "institution_id": None})()

    result = await service.approve_record(
        record.id,
        CurationActionRequest(note="Reviewed and corrected"),
        actor_user,
    )

    assert result.record_state == "validated"
    assert result.validated_at is not None
    assert result.review_notes == "Reviewed and corrected"
    assert len(session.added) == 1


async def test_curation_service_publish_and_unpublish_follow_allowed_path():
    session = FakeSession()
    service = CurationService(session)
    record = make_record(RecordState.VALIDATED)

    async def fake_load_record(_record_id, _actor_user):
        return record

    service._load_record = fake_load_record  # type: ignore[method-assign]

    actor_user = type("U", (), {"id": uuid4(), "role": UserRole.ADMIN, "institution_id": None})()

    published = await service.publish_record(
        record.id,
        CurationActionRequest(note="Ready for students"),
        actor_user,
    )
    assert published.record_state == "published"
    assert published.published_at is not None

    unpublished = await service.unpublish_record(
        record.id,
        CurationActionRequest(note="Pulled for revision"),
        actor_user,
    )
    assert unpublished.record_state == "validated"
    assert unpublished.unpublished_at is not None


async def test_curation_service_rejects_invalid_publish_transition():
    session = FakeSession()
    service = CurationService(session)
    record = make_record(RecordState.RAW)

    async def fake_load_record(_record_id, _actor_user):
        return record

    service._load_record = fake_load_record  # type: ignore[method-assign]

    actor_user = type("U", (), {"id": uuid4(), "role": UserRole.ADMIN, "institution_id": None})()

    with pytest.raises(HTTPException) as caught:
        await service.publish_record(
            record.id,
            CurationActionRequest(note="Should fail"),
            actor_user,
        )

    assert caught.value.status_code == 409


async def test_curation_service_import_raw_record_creates_internal_raw_state():
    session = FakeSession()
    service = CurationService(session)
    actor_user_id = uuid4()
    actor_user = type("U", (), {"id": actor_user_id, "role": UserRole.ADMIN, "institution_id": None})()

    async def fake_source_registry(_payload, _actor_user):
        return SourceRegistry(
            source_key="manual_demo_import",
            display_name="Manual demo import",
            base_url="https://example.edu",
            source_type="manual_import",
            institution_id=None,
            is_active=True,
        )

    service._get_or_create_source_registry = fake_source_registry  # type: ignore[method-assign]

    result = await service.import_raw_record(
        CurationRawImportRequest(
            source_key="manual_demo_import",
            source_display_name="Manual demo import",
            source_base_url="https://example.edu",
            source_type="manual_import",
            title="UBC Data Science Award",
            provider_name="University of British Columbia",
            country_code="CA",
            source_url="https://example.edu/ubc-data-science-award",
            summary="Imported raw summary",
            field_tags=["data science"],
            degree_levels=["MS"],
            citizenship_rules=["PK"],
            review_notes="Imported for curator review",
        ),
        actor_user,
    )

    assert result.record_state == "raw"
    assert result.review_notes == "Imported for curator review"
    assert result.reviewed_by_user_id == str(actor_user_id)
    assert any(getattr(item, "action", "") == "curation.import_raw" for item in session.added)
