from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
import httpx
from fastapi import HTTPException

from app.models import IngestionRun, IngestionRunStatus, SourceRegistry, UserRole
from app.schemas.curation import (
    IngestionRunDetail,
    IngestionRunBulkRetryRequest,
    IngestionRunQueueAssignmentRequest,
    IngestionRunRetryRequest,
    IngestionRunStartRequest,
)
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


async def test_start_run_creates_candidate_from_jsonld_when_no_anchor_candidates(monkeypatch):
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
                <title>Structured Funding</title>
                <script type="application/ld+json">
                {
                  "@context": "https://schema.org",
                  "@type": "Scholarship",
                  "name": "Structured Data Science Scholarship",
                  "description": "Scholarship support for data science master's applicants with analytics experience.",
                  "url": "/awards/structured-data-science-scholarship"
                }
                </script>
              </head>
              <body>
                <p>No traditional scholarship links are rendered in anchors.</p>
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
    assert payload.title == "Structured Data Science Scholarship"
    assert str(payload.source_url).endswith("/awards/structured-data-science-scholarship")
    assert payload.provenance_payload["parse_origin"] == "jsonld"
    assert detail.run_metadata["parser"]["jsonld_candidates"] == 1
    assert detail.run_metadata["parser"]["anchor_candidates"] == 0
    assert getattr(imported_actor, "id", None) == actor_user_id


async def test_start_run_creates_candidates_from_jsonld_itemlist_with_main_entity_url(monkeypatch):
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
                <title>Structured List Funding</title>
                <script type="application/ld+json">
                {
                  "@context": "https://schema.org",
                  "@type": "ItemList",
                  "itemListElement": [
                    {
                      "@type": "ListItem",
                      "position": 1,
                      "item": {
                        "@type": "Scholarship",
                        "name": "Nested Structured Analytics Scholarship",
                        "description": "Funding for analytics and data science master's study.",
                        "mainEntityOfPage": {
                          "@type": "WebPage",
                          "@id": "/awards/nested-structured-analytics-scholarship"
                        }
                      }
                    }
                  ]
                }
                </script>
              </head>
              <body>
                <p>Scholarship data is emitted through structured list metadata only.</p>
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
    assert payload.title == "Nested Structured Analytics Scholarship"
    assert str(payload.source_url).endswith("/awards/nested-structured-analytics-scholarship")
    assert payload.provenance_payload["parse_origin"] == "jsonld"
    assert detail.run_metadata["parser"]["jsonld_candidates"] == 1
    assert getattr(imported_actor, "id", None) == actor_user_id


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


async def test_retry_run_updates_retry_metadata_and_executes_inline(monkeypatch):
    session = FakeSession()
    session.source = make_source()
    service = IngestionService(session)
    actor = SimpleNamespace(id=uuid4(), role=UserRole.ADMIN, institution_id=None)
    run_id = uuid4()
    run = IngestionRun(
        id=run_id,
        source_registry=session.source,
        source_registry_id=session.source.id,
        triggered_by_user_id=actor.id,
        institution_id=None,
        status=IngestionRunStatus.FAILED,
        fetch_url=str(session.source.base_url),
    )
    run.run_metadata = {
        "request": {"max_records": 5, "execution_mode_requested": "worker"},
        "execution": {"attempt_count": 1, "run_retry_count": 0, "selected_mode": "worker"},
    }
    run.created_at = datetime.now(timezone.utc)
    run.updated_at = datetime.now(timezone.utc)
    session.run = run
    session.source = session.source

    async def execute_for_run(_query):
        return FakeResult(run)

    session.execute = execute_for_run

    captured_execute = {}

    async def fake_execute_run(
        _run_id,
        *,
        actor_user_id,
        max_records,
        execution_context,
        persist_running_state=False,
    ):
        captured_execute["run_id"] = _run_id
        captured_execute["actor_user_id"] = actor_user_id
        captured_execute["max_records"] = max_records
        captured_execute["execution_context"] = execution_context
        captured_execute["persist_running_state"] = persist_running_state
        return service._build_detail(run)

    monkeypatch.setattr(service, "execute_run", fake_execute_run)

    detail = await service.retry_run(
        run_id,
        payload=IngestionRunRetryRequest(max_records=3, execution_mode="inline"),
        actor_user=actor,
    )

    assert captured_execute["run_id"] == run_id
    assert captured_execute["actor_user_id"] == actor.id
    assert captured_execute["max_records"] == 3
    assert captured_execute["execution_context"]["dispatch_status"] == "retry_inline"
    assert detail.run_metadata["execution"]["run_retry_count"] == 1
    assert detail.run_metadata["request"]["execution_mode_requested"] == "inline"
    assert detail.run_metadata["execution"]["last_retry_requested_at"] is not None


async def test_retry_run_rejects_running_status():
    session = FakeSession()
    session.source = make_source()
    service = IngestionService(session)
    actor = SimpleNamespace(id=uuid4(), role=UserRole.ADMIN, institution_id=None)
    run_id = uuid4()
    run = IngestionRun(
        id=run_id,
        source_registry=session.source,
        source_registry_id=session.source.id,
        triggered_by_user_id=actor.id,
        institution_id=None,
        status=IngestionRunStatus.RUNNING,
        fetch_url=str(session.source.base_url),
    )
    run.run_metadata = {"request": {"max_records": 5}}
    run.created_at = datetime.now(timezone.utc)
    run.updated_at = datetime.now(timezone.utc)
    session.run = run
    session.source = session.source

    async def execute_for_run(_query):
        return FakeResult(run)

    session.execute = execute_for_run

    with pytest.raises(HTTPException) as caught:
        await service.retry_run(
            run_id,
            payload=IngestionRunRetryRequest(),
            actor_user=actor,
        )

    assert caught.value.status_code == 409
    assert "cannot be retried" in str(caught.value.detail)


async def test_retry_run_rejects_cross_institution_scope():
    session = FakeSession()
    session.source = make_source()
    service = IngestionService(session)
    run_id = uuid4()
    run = IngestionRun(
        id=run_id,
        source_registry=session.source,
        source_registry_id=session.source.id,
        triggered_by_user_id=uuid4(),
        institution_id=uuid4(),
        status=IngestionRunStatus.FAILED,
        fetch_url=str(session.source.base_url),
    )
    run.run_metadata = {"request": {"max_records": 5}}
    run.created_at = datetime.now(timezone.utc)
    run.updated_at = datetime.now(timezone.utc)
    session.run = run
    session.source = session.source

    async def execute_for_run(_query):
        return FakeResult(run)

    session.execute = execute_for_run
    actor = SimpleNamespace(id=uuid4(), role=UserRole.UNIVERSITY, institution_id=uuid4())

    with pytest.raises(HTTPException) as caught:
        await service.retry_run(
            run_id,
            payload=IngestionRunRetryRequest(),
            actor_user=actor,
        )

    assert caught.value.status_code == 403
    assert "outside institution scope" in str(caught.value.detail)


async def test_list_runs_filters_by_status_source_and_dispatch():
    session = FakeSession()
    service = IngestionService(session)
    source_one = make_source()
    source_two = make_source()
    source_two.source_key = "fulbright-foreign-student"

    run_a = IngestionRun(
        id=uuid4(),
        source_registry=source_one,
        source_registry_id=source_one.id,
        triggered_by_user_id=uuid4(),
        institution_id=None,
        status=IngestionRunStatus.PARTIAL,
        fetch_url=str(source_one.base_url),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        run_metadata={"execution": {"dispatch_status": "queued"}},
    )
    run_b = IngestionRun(
        id=uuid4(),
        source_registry=source_two,
        source_registry_id=source_two.id,
        triggered_by_user_id=uuid4(),
        institution_id=None,
        status=IngestionRunStatus.FAILED,
        fetch_url=str(source_two.base_url),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        run_metadata={"execution": {"dispatch_status": "retry_inline"}},
    )

    class ListResult:
        def __init__(self, runs):
            self._runs = runs

        def scalars(self):
            return SimpleNamespace(all=lambda: self._runs)

    async def fake_execute(_query):
        return ListResult([run_a, run_b])

    session.execute = fake_execute

    filtered = await service.list_runs(
        actor_user=SimpleNamespace(id=uuid4(), role=UserRole.ADMIN, institution_id=None),
        status_filter="failed",
        source_key="fulbright-foreign-student",
        dispatch_status="retry_inline",
    )

    assert filtered.total == 1
    assert filtered.items[0].status == "failed"
    assert filtered.items[0].source_key == "fulbright-foreign-student"
    assert filtered.items[0].dispatch_status == "retry_inline"


async def test_list_runs_rejects_invalid_status_filter():
    session = FakeSession()
    service = IngestionService(session)

    with pytest.raises(HTTPException) as caught:
        await service.list_runs(
            actor_user=SimpleNamespace(id=uuid4(), role=UserRole.ADMIN, institution_id=None),
            status_filter="not_a_status",
        )

    assert caught.value.status_code == 400


async def test_assign_review_queue_sets_execution_metadata():
    session = FakeSession()
    session.source = make_source()
    service = IngestionService(session)
    actor = SimpleNamespace(id=uuid4(), role=UserRole.ADMIN, institution_id=None)
    run = IngestionRun(
        id=uuid4(),
        source_registry=session.source,
        source_registry_id=session.source.id,
        triggered_by_user_id=actor.id,
        institution_id=None,
        status=IngestionRunStatus.PARTIAL,
        fetch_url=str(session.source.base_url),
    )
    run.run_metadata = {"execution": {}}
    run.created_at = datetime.now(timezone.utc)
    run.updated_at = datetime.now(timezone.utc)
    session.run = run

    async def execute_for_run(_query):
        return FakeResult(run)

    session.execute = execute_for_run

    detail = await service.assign_review_queue(
        run.id,
        payload=IngestionRunQueueAssignmentRequest(queue_key="manual-review", note="needs escalation"),
        actor_user=actor,
    )

    execution = detail.run_metadata["execution"]
    assert execution["review_queue"] == "manual-review"
    assert execution["queue_assignment_note"] == "needs escalation"
    assert execution["queue_assigned_by_user_id"] == str(actor.id)
    assert execution["queue_assigned_at"] is not None


async def test_get_and_clear_run_snapshot():
    session = FakeSession()
    session.source = make_source()
    service = IngestionService(session)
    actor = SimpleNamespace(id=uuid4(), role=UserRole.ADMIN, institution_id=None)
    run = IngestionRun(
        id=uuid4(),
        source_registry=session.source,
        source_registry_id=session.source.id,
        triggered_by_user_id=actor.id,
        institution_id=None,
        status=IngestionRunStatus.PARTIAL,
        fetch_url=str(session.source.base_url),
    )
    run.run_metadata = {
        "snapshot": {
            "html_content": "<html><body>Captured</body></html>",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "content_length": 34,
            "truncated": False,
        }
    }
    run.created_at = datetime.now(timezone.utc)
    run.updated_at = datetime.now(timezone.utc)
    session.run = run

    async def execute_for_run(_query):
        return FakeResult(run)

    session.execute = execute_for_run

    snapshot = await service.get_run_snapshot(run.id, actor_user=actor)
    assert snapshot.available is True
    assert snapshot.html_content is not None
    assert snapshot.content_length == 34

    cleared = await service.clear_run_snapshot(run.id, actor_user=actor)
    assert cleared.available is False
    assert cleared.html_content is None
    assert cleared.content_length == 0
    assert run.run_metadata["snapshot"]["html_content"] is None


async def test_bulk_retry_runs_returns_mixed_results(monkeypatch):
    session = FakeSession()
    service = IngestionService(session)
    actor = SimpleNamespace(id=uuid4(), role=UserRole.ADMIN, institution_id=None)
    run_ok = str(uuid4())
    run_skip = str(uuid4())

    async def fake_retry(run_id, *, payload, actor_user):
        if str(run_id) == run_ok:
            return IngestionRunDetail(
                run_id=run_ok,
                source_key="waterloo-awards",
                source_display_name="Waterloo",
                fetch_url="https://example.test",
                status="partial",
                capture_mode=None,
                parser_name=None,
                records_found=1,
                records_created=1,
                records_skipped=0,
                failure_reason=None,
                started_at=None,
                completed_at=None,
                created_at=datetime.now(timezone.utc),
                execution_mode_requested="inline",
                execution_mode_selected="inline",
                dispatch_status="retry_inline",
                celery_task_id=None,
                attempt_count=1,
                run_retry_count=1,
                last_started_at=None,
                last_retry_requested_at=None,
                failure_phase=None,
                review_queue=None,
                queue_assigned_by_user_id=None,
                queue_assigned_at=None,
                queue_assignment_note=None,
                snapshot_available=False,
                snapshot_captured_at=None,
                snapshot_content_length=None,
                run_metadata={},
            )
        if str(run_id) == run_skip:
            raise HTTPException(status_code=409, detail="already running")
        raise HTTPException(status_code=404, detail="not found")

    monkeypatch.setattr(service, "retry_run", fake_retry)

    response = await service.bulk_retry_runs(
        payload=IngestionRunBulkRetryRequest(
            run_ids=[run_ok, run_skip, "bad-uuid"],
            max_records=3,
            execution_mode="inline",
        ),
        actor_user=actor,
    )

    assert response.total == 3
    assert response.retried == 1
    assert response.skipped == 1
    assert response.failed == 1


class ExceptionWrapper:
    http_status_error_type = httpx.HTTPStatusError

    @staticmethod
    def http_status_error(*, request, response):
        return httpx.HTTPStatusError("bad request", request=request, response=response)
