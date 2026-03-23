from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
import httpx

from app.models import IngestionRun, IngestionRunStatus, SourceRegistry, UserRole
from app.schemas.curation import IngestionRunStartRequest
from app.services.ingestion.service import (
    CaptureResult,
    IngestionService,
    retry_async,
)

pytestmark = pytest.mark.asyncio


class FakeSession:
    def __init__(self):
        self.added = []
        self.run = None
        self.source = None
        self.execute_calls = 0

    async def execute(self, _query):
        self.execute_calls += 1
        if self.run is not None and self.execute_calls > 1:
            return FakeResult(self.run)
        return FakeResult(self.source)

    def add(self, value):
        if getattr(value, "id", None) is None:
            value.id = uuid4()
        if getattr(value, "created_at", None) is None:
            value.created_at = datetime.now(timezone.utc)
        if getattr(value, "updated_at", None) is None:
            value.updated_at = datetime.now(timezone.utc)
        if isinstance(value, IngestionRun):
            self.run = value
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


def make_capture(
    html: str,
    *,
    final_url: str | None = None,
    title: str | None = "Graduate Funding",
) -> CaptureResult:
    return CaptureResult(
        html=html,
        final_url=final_url or "https://uwaterloo.ca/graduate-studies-postdoctoral-affairs/funding",
        title=title,
        capture_mode="httpx_fallback",
        metadata={
            "requested_url": final_url or "https://uwaterloo.ca/graduate-studies-postdoctoral-affairs/funding",
            "status_code": 200,
        },
    )


async def test_start_run_creates_raw_record_from_source_page(monkeypatch):
    session = FakeSession()
    session.source = make_source()
    service = IngestionService(session)
    actor_user_id = uuid4()
    captured_calls = []

    async def fake_capture(_url: str) -> CaptureResult:
        capture = make_capture(
            """
            <html>
              <head>
                <title>Funding</title>
                <meta name="description" content="Funding for data science master's students." />
              </head>
              <body>
                <a href="/awards/data-science-scholarship">Data Science Scholarship</a>
              </body>
            </html>
            """
        )
        capture.metadata.update(
            {
                "retry_policy": {
                    "max_attempts": 2,
                    "base_delay_seconds": 0.75,
                },
                "attempt": 1,
                "max_attempts": 2,
                "retries_used": 0,
                "attempt_errors": [],
            }
        )
        return capture

    class RecordingCurationService:
        def __init__(self, _db):
            pass

        async def import_raw_record(self, payload, actor_id):
            captured_calls.append((payload, actor_id))
            return SimpleNamespace(
                record_id=str(uuid4()),
                title=payload.title,
                source_url=str(payload.source_url),
            )

    monkeypatch.setattr(service, "_capture_source", fake_capture)
    monkeypatch.setattr(
        "app.services.ingestion.service.CurationService",
        RecordingCurationService,
    )

    detail = await service.start_run(
        IngestionRunStartRequest(source_key=session.source.source_key, max_records=5),
        actor_user_id,
    )

    payload, imported_actor = captured_calls[0]
    assert detail.status == IngestionRunStatus.COMPLETED.value
    assert detail.records_found == 1
    assert detail.records_created == 1
    assert detail.records_skipped == 0
    assert detail.run_metadata["capture"]["status_code"] == 200
    assert detail.run_metadata["capture"]["attempt"] == 1
    assert detail.run_metadata["capture"]["max_attempts"] == 2
    assert detail.run_metadata["capture"]["retries_used"] == 0
    assert detail.run_metadata["capture"]["retry_policy"]["max_attempts"] == 2
    assert detail.run_metadata["execution"]["attempt_count"] == 1
    assert detail.run_metadata["execution"]["retry_count"] == 0
    assert detail.run_metadata["created_records"][0]["title"] == "Data Science Scholarship"
    assert getattr(imported_actor, "id", None) == actor_user_id
    assert payload.title == "Data Science Scholarship"
    assert str(payload.source_url).endswith("/awards/data-science-scholarship")
    assert payload.source_document_ref == "data-science-scholarship"
    assert payload.field_tags == ["data science"]
    assert payload.degree_levels == ["MS"]
    assert payload.review_notes == "Auto-imported from source registry page for curator review."
    assert payload.provenance_payload["ingested_via"] == "source_registry_run"


async def test_start_run_marks_duplicates_as_skipped(monkeypatch):
    session = FakeSession()
    session.source = make_source()
    service = IngestionService(session)
    actor_user = type("U", (), {"id": uuid4(), "role": UserRole.ADMIN, "institution_id": None})()

    async def fake_capture(_url: str) -> CaptureResult:
        return make_capture(
            """
            <html>
              <head>
                <title>Funding</title>
                <meta name="description" content="Funding for data science and analytics students." />
              </head>
              <body>
                <a href="/awards/data-science-scholarship">Data Science Scholarship</a>
                <a href="/awards/analytics-award">Analytics Award</a>
              </body>
            </html>
            """
        )

    class RecordingCurationService:
        def __init__(self, _db):
            self.calls = []

        async def import_raw_record(self, payload, actor_id):
            self.calls.append((payload, actor_id))
            return SimpleNamespace(
                record_id=str(uuid4()),
                title=payload.title,
                source_url=str(payload.source_url),
            )

    existing = SimpleNamespace(
        id=uuid4(),
        title="Data Science Scholarship",
        source_url="https://uwaterloo.ca/awards/data-science-scholarship",
        source_document_ref="data-science-scholarship",
        content_hash="hash-1",
    )

    async def fake_find_existing(where_clause):
        left = getattr(where_clause, "left", None)
        right = getattr(where_clause, "right", None)
        key = getattr(left, "key", None)
        value = getattr(right, "value", None)
        if (
            key == "source_url"
            and isinstance(value, str)
            and value.endswith("/awards/data-science-scholarship")
        ):
            return existing
        return None

    monkeypatch.setattr(service, "_capture_source", fake_capture)
    monkeypatch.setattr(service, "_find_existing_scholarship", fake_find_existing)
    monkeypatch.setattr(
        "app.services.ingestion.service.CurationService",
        RecordingCurationService,
    )

    detail = await service.start_run(
        IngestionRunStartRequest(source_key=session.source.source_key, max_records=5),
        actor_user,
    )

    assert detail.status == IngestionRunStatus.PARTIAL.value
    assert detail.records_found == 2
    assert detail.records_created == 1
    assert detail.records_skipped == 1
    assert detail.run_metadata["created_records"][0]["title"] == "Analytics Award"
    assert detail.run_metadata["dedup"]["source_url_matches"] == 1
    assert detail.run_metadata["skipped_records"][0]["reason"] == "duplicate_source_url"


async def test_retry_async_retries_flaky_coroutine(monkeypatch):
    sleep_calls = []

    async def fake_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.setattr("app.services.ingestion.service.asyncio.sleep", fake_sleep)

    attempts = {"count": 0}

    @retry_async(max_retries=3, delay=0.5)
    async def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary capture failure")
        return "ok"

    result = await flaky()

    assert result == "ok"
    assert attempts["count"] == 3
    assert sleep_calls == [0.5, 1.0]


async def test_start_run_records_failure_metadata_when_capture_fails(monkeypatch):
    session = FakeSession()
    session.source = make_source()
    service = IngestionService(session)

    async def failing_capture(_url: str) -> CaptureResult:
        raise RuntimeError("capture unavailable")

    monkeypatch.setattr(service, "_capture_source", failing_capture)

    with pytest.raises(RuntimeError, match="capture unavailable"):
        await service.start_run(
            IngestionRunStartRequest(source_key=session.source.source_key, max_records=5),
            uuid4(),
        )

    run = session.run
    assert run is not None
    assert run.status == IngestionRunStatus.FAILED
    assert run.failure_reason == "capture unavailable"
    assert run.run_metadata["error_type"] == "RuntimeError"
    assert run.run_metadata["failure"]["phase"] == "capture_or_parse"
    assert run.run_metadata["failure"]["error_message"] == "capture unavailable"


async def test_capture_source_stops_retrying_on_non_retryable_error(monkeypatch):
    session = FakeSession()
    service = IngestionService(session)
    attempts = {"count": 0}

    async def always_bad_request(_url: str, _attempt: int):
        attempts["count"] += 1
        request = SimpleNamespace(url="https://example.com/scholarships")
        response = SimpleNamespace(status_code=400)
        raise ExceptionWrapper.http_status_error(request=request, response=response)

    monkeypatch.setattr(service, "_capture_source_once", always_bad_request)

    with pytest.raises(ExceptionWrapper.http_status_error_type):
        await service._capture_source("https://example.com/scholarships")

    assert attempts["count"] == 1


async def test_capture_source_non_retryable_error_attaches_classified_attempt_metadata(monkeypatch):
    session = FakeSession()
    service = IngestionService(session)

    async def always_bad_request(_url: str, attempt: int):
        assert attempt == 1
        request = SimpleNamespace(url="https://example.com/scholarships")
        response = SimpleNamespace(status_code=400)
        raise ExceptionWrapper.http_status_error(request=request, response=response)

    monkeypatch.setattr(service, "_capture_source_once", always_bad_request)

    with pytest.raises(ExceptionWrapper.http_status_error_type) as caught:
        await service._capture_source("https://example.com/scholarships")

    attempt_errors = getattr(caught.value, "_capture_attempts", None)
    assert attempt_errors is not None
    assert len(attempt_errors) == 1
    assert attempt_errors[0]["attempt"] == 1
    assert attempt_errors[0]["classification"] == "client_http_status"
    assert attempt_errors[0]["retryable"] is False


async def test_capture_source_retries_retryable_error_and_includes_retry_policy(monkeypatch):
    session = FakeSession()
    service = IngestionService(session)
    attempts = {"count": 0}
    sleep_calls = []

    async def flaky_capture(_url: str, _attempt: int):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise httpx.ReadTimeout("temporary timeout")
        return make_capture("<html><title>OK</title></html>")

    async def fake_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.setattr(service, "_capture_source_once", flaky_capture)
    monkeypatch.setattr("app.services.ingestion.service.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("app.services.ingestion.service.random.uniform", lambda _a, _b: 0.0)

    capture = await service._capture_source("https://example.com/scholarships")

    assert attempts["count"] == 2
    assert sleep_calls == [0.75]
    assert capture.metadata["retry_policy"]["max_attempts"] == 2
    assert capture.metadata["retry_policy"]["base_delay_seconds"] == 0.75
    assert capture.metadata["attempt_errors"][0]["classification"] == "timeout"
    assert capture.metadata["attempt_errors"][0]["retryable"] is True


class ExceptionWrapper:
    http_status_error_type = httpx.HTTPStatusError

    @staticmethod
    def http_status_error(*, request, response):
        return httpx.HTTPStatusError("bad request", request=request, response=response)
