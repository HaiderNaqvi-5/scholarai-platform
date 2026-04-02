from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models import ApplicationStatus, RecordState
from app.services.saved_opportunities import SavedOpportunityService

pytestmark = pytest.mark.asyncio


class ScalarResult:
    def __init__(self, one=None, all_items=None):
        self.one = one
        self.all_items = all_items or []

    def scalar_one_or_none(self):
        return self.one

    def scalars(self):
        return self

    def all(self):
        return self.all_items


class FakeSession:
    def __init__(self, results):
        self.results = list(results)
        self.added = []
        self.execute_calls = 0

    async def execute(self, _query):
        self.execute_calls += 1
        return self.results.pop(0) if self.results else ScalarResult()

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None

    async def refresh(self, value):
        value.id = uuid4()
        value.created_at = datetime.now(timezone.utc)


async def test_saved_opportunities_service_filters_to_published_records():
    user_id = uuid4()
    published = SimpleNamespace(
        id=uuid4(),
        title="Published Scholarship",
        provider_name="Provider",
        country_code="CA",
        deadline_at=None,
        record_state=RecordState.PUBLISHED,
        source_url="https://example.com/ca/scholarship",
        summary="Published summary",
    )
    validated = SimpleNamespace(
        id=uuid4(),
        title="Validated Only",
        provider_name="Provider",
        country_code="CA",
        deadline_at=None,
        record_state=RecordState.VALIDATED,
        source_url="https://example.com/ca/validated",
        summary="Validated summary",
    )
    session = FakeSession(
        [
            ScalarResult(
                all_items=[
                    SimpleNamespace(
                        scholarship=published,
                        status=ApplicationStatus.SAVED,
                        created_at=datetime.now(timezone.utc),
                    ),
                    SimpleNamespace(
                        scholarship=validated,
                        status=ApplicationStatus.SAVED,
                        created_at=datetime.now(timezone.utc),
                    ),
                ]
            )
        ]
    )

    service = SavedOpportunityService(session)
    items = await service.list_saved(user_id)

    assert len(items) == 1
    assert items[0].title == "Published Scholarship"
    assert items[0].record_state == "published"


async def test_saved_opportunities_service_save_rejects_unpublished_records():
    session = FakeSession([ScalarResult(one=None)])
    service = SavedOpportunityService(session)

    with pytest.raises(HTTPException) as caught:
        await service.save(uuid4(), uuid4())

    assert caught.value.status_code == 404


async def test_saved_opportunities_service_save_creates_entry_for_published_record():
    scholarship_id = uuid4()
    scholarship = SimpleNamespace(
        id=scholarship_id,
        title="Published Scholarship",
        provider_name="Provider",
        country_code="CA",
        deadline_at=None,
        record_state=RecordState.PUBLISHED,
        source_url="https://example.com/ca/scholarship",
        summary="Published summary",
    )
    session = FakeSession(
        [
            ScalarResult(one=scholarship),
            ScalarResult(one=None),
        ]
    )
    service = SavedOpportunityService(session)

    item = await service.save(uuid4(), scholarship_id)

    assert item.scholarship_id == str(scholarship_id)
    assert item.record_state == "published"
    assert len(session.added) == 1
    assert item.tracker_status == "saved"


async def test_saved_opportunities_service_update_status_updates_tracker_state():
    scholarship_id = uuid4()
    scholarship = SimpleNamespace(
        id=scholarship_id,
        title="Published Scholarship",
        provider_name="Provider",
        country_code="CA",
        deadline_at=None,
        record_state=RecordState.PUBLISHED,
        source_url="https://example.com/ca/scholarship",
        summary="Published summary",
    )
    session = FakeSession(
        [
            ScalarResult(
                one=SimpleNamespace(
                    id=uuid4(),
                    scholarship_id=scholarship_id,
                    scholarship=scholarship,
                    status=ApplicationStatus.SAVED,
                    created_at=datetime.now(timezone.utc),
                )
            )
        ]
    )
    service = SavedOpportunityService(session)

    item = await service.update_status(uuid4(), scholarship_id, "applied")

    assert item.scholarship_id == str(scholarship_id)
    assert item.tracker_status == "applied"


async def test_saved_opportunities_service_update_status_raises_when_missing():
    session = FakeSession([ScalarResult(one=None)])
    service = SavedOpportunityService(session)

    with pytest.raises(HTTPException) as caught:
        await service.update_status(uuid4(), uuid4(), "in_progress")

    assert caught.value.status_code == 404


async def test_saved_opportunities_service_remove_deletes_existing_saved_entry():
    application_id = uuid4()
    session = FakeSession(
        [
            ScalarResult(
                one=SimpleNamespace(
                    id=application_id,
                    scholarship_id=uuid4(),
                )
            )
        ]
    )
    service = SavedOpportunityService(session)

    await service.remove(uuid4(), uuid4())

    assert session.execute_calls == 2
