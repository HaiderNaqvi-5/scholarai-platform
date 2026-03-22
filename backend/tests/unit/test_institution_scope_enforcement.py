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


async def test_ingestion_list_runs_invokes_database_query():
    service = IngestionService(NoopSession())

    with pytest.raises(AssertionError, match="DB execute should not be reached"):
        await service.list_runs()


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


async def test_get_or_create_source_returns_existing_source():
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
        source_display_name="Shared Source",
        source_base_url="https://example.com",
        source_type="official",
    )

    resolved = await service._get_or_create_source(payload)
    assert resolved is source
