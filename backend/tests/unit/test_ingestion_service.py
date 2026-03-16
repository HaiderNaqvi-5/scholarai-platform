from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models import IngestionRunStatus, SourceRegistry
from app.schemas.curation import IngestionRunStartRequest
from app.services.ingestion.service import CaptureResult, IngestionService

pytestmark = pytest.mark.asyncio


class FakeSession:
    def __init__(self):
        self.added = []
        self.source = None

    async def execute(self, _query):
        return FakeResult(self.source)

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


def make_source() -> SourceRegistry:
    source = SourceRegistry(
        source_key="waterloo-awards",
        display_name="University of Waterloo Graduate Funding",
        base_url="https://uwaterloo.ca/graduate-studies-postdoctoral-affairs/funding",
        source_type="official",
        is_active=True,
    )
    source.id = uuid4()
    source.created_at = datetime.now(timezone.utc)
    source.updated_at = datetime.now(timezone.utc)
    return source


async def test_parse_candidates_extracts_scholarship_like_links():
    service = IngestionService(FakeSession())
    source = make_source()
    capture = CaptureResult(
        html="""
        <html>
          <head>
            <title>Graduate Funding</title>
            <meta name="description" content="Data science and AI graduate scholarships for master's students." />
          </head>
          <body>
            <a href="/awards/data-science-scholarship">Data Science Scholarship</a>
            <a href="/awards/analytics-award">Analytics Award</a>
          </body>
        </html>
        """,
        final_url=source.base_url,
        title="Graduate Funding",
        capture_mode="httpx_fallback",
        metadata={},
    )

    candidates = service._parse_candidates(source, capture)

    assert len(candidates) == 2
    assert candidates[0].country_code == "CA"
    assert "data science" in candidates[0].field_tags
    assert candidates[0].degree_levels == ["MS"]


async def test_start_run_records_created_and_partial_status(monkeypatch):
    session = FakeSession()
    session.source = make_source()
    service = IngestionService(session)
    actor_user_id = uuid4()

    async def fake_capture(_url: str) -> CaptureResult:
        return CaptureResult(
            html="""
            <html>
              <head><title>Funding</title></head>
              <body>
                <a href="/awards/data-science-scholarship">Data Science Scholarship</a>
                <a href="/awards/analytics-award">Analytics Award</a>
              </body>
            </html>
            """,
            final_url=session.source.base_url,
            title="Funding",
            capture_mode="httpx_fallback",
            metadata={},
        )

    class FakeCurationService:
        call_count = 0

        def __init__(self, _db):
            pass

        async def import_raw_record(self, payload, actor_id):
            FakeCurationService.call_count += 1
            if FakeCurationService.call_count == 1:
                return type(
                    "Detail",
                    (),
                    {
                        "record_id": str(uuid4()),
                        "title": payload.title,
                        "source_url": payload.source_url,
                    },
                )()
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="duplicate",
            )

    monkeypatch.setattr(service, "_capture_source", fake_capture)
    monkeypatch.setattr(
        "app.services.ingestion.service.CurationService",
        FakeCurationService,
    )

    detail = await service.start_run(
        IngestionRunStartRequest(source_key=session.source.source_key, max_records=5),
        actor_user_id,
    )

    assert detail.status == IngestionRunStatus.PARTIAL.value
    assert detail.records_created == 1
    assert detail.records_skipped == 1
