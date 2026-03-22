from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models import UserRole
from app.services.curation import CurationService
from app.services.ingestion import IngestionService

pytestmark = pytest.mark.asyncio


class NoopSession:
    async def execute(self, _query):
        raise AssertionError("DB execute should not be reached for missing scope checks")


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class SourceSession:
    def __init__(self, source):
        self._source = source

    async def execute(self, _query):
        return _Result(self._source)


async def test_curation_list_records_requires_institution_for_university_user():
    service = CurationService(NoopSession())
    user = SimpleNamespace(id=uuid4(), role=UserRole.UNIVERSITY, institution_id=None)

    with pytest.raises(HTTPException) as caught:
        await service.list_records(user)

    assert caught.value.status_code == 403


class _ScalarList:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _ListResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _ScalarList(self._items)


class ListRunsSession:
    async def execute(self, _query):
        return _ListResult([])


async def test_ingestion_list_runs_accepts_limit_parameter():
    service = IngestionService(ListRunsSession())
    response = await service.list_runs(limit=10)

    assert response.total == 0
    assert response.items == []


async def test_curation_rejects_cross_institution_source_registry_access():
    actor_institution = uuid4()
    source = SimpleNamespace(
        source_key="shared_source",
        display_name="Shared Source",
        base_url="https://example.com",
        source_type="official",
        institution_id=uuid4(),
        is_active=True,
    )
    service = CurationService(SourceSession(source))
    actor = SimpleNamespace(id=uuid4(), role=UserRole.UNIVERSITY, institution_id=actor_institution)
    payload = SimpleNamespace(
        source_key="shared_source",
        source_display_name="Shared Source",
        source_base_url="https://example.com",
        source_type="official",
    )

    with pytest.raises(HTTPException) as caught:
        await service._get_or_create_source_registry(payload, actor)

    assert caught.value.status_code == 403


async def test_ingestion_get_or_create_source_updates_existing_source():
    source = SimpleNamespace(
        source_key="shared_source",
        display_name="Shared Source",
        base_url="https://example.com",
        source_type="official",
        institution_id=uuid4(),
        is_active=True,
    )
    service = IngestionService(SourceSession(source))
    payload = SimpleNamespace(
        source_key="shared_source",
        source_display_name="Updated Source",
        source_base_url="https://updated.example.com",
        source_type="partner",
    )

    updated_source = await service._get_or_create_source(payload)

    assert updated_source is source
    assert source.display_name == "Updated Source"
    assert source.base_url == "https://updated.example.com"
    assert source.source_type == "partner"
