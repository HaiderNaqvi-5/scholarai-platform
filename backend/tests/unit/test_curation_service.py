from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models import RecordState, Scholarship
from app.schemas.curation import CurationActionRequest
from app.services.curation import CurationService

pytestmark = pytest.mark.asyncio


class FakeSession:
    def __init__(self):
        self.added = []

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

    async def flush(self):
        return None


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

    async def fake_load_record(_record_id):
        return record

    service._load_record = fake_load_record  # type: ignore[method-assign]

    result = await service.approve_record(
        record.id,
        CurationActionRequest(note="Reviewed and corrected"),
        uuid4(),
    )

    assert result.record_state == "validated"
    assert result.validated_at is not None
    assert result.review_notes == "Reviewed and corrected"
    assert len(session.added) == 1


async def test_curation_service_publish_and_unpublish_follow_allowed_path():
    session = FakeSession()
    service = CurationService(session)
    record = make_record(RecordState.VALIDATED)

    async def fake_load_record(_record_id):
        return record

    service._load_record = fake_load_record  # type: ignore[method-assign]

    published = await service.publish_record(
        record.id,
        CurationActionRequest(note="Ready for students"),
        uuid4(),
    )
    assert published.record_state == "published"
    assert published.published_at is not None

    unpublished = await service.unpublish_record(
        record.id,
        CurationActionRequest(note="Pulled for revision"),
        uuid4(),
    )
    assert unpublished.record_state == "validated"
    assert unpublished.unpublished_at is not None


async def test_curation_service_rejects_invalid_publish_transition():
    session = FakeSession()
    service = CurationService(session)
    record = make_record(RecordState.RAW)

    async def fake_load_record(_record_id):
        return record

    service._load_record = fake_load_record  # type: ignore[method-assign]

    with pytest.raises(HTTPException) as caught:
        await service.publish_record(
            record.id,
            CurationActionRequest(note="Should fail"),
            uuid4(),
        )

    assert caught.value.status_code == 409
