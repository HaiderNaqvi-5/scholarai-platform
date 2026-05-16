from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
import httpx
from fastapi import HTTPException

from app.models import IngestionRun, IngestionRunStatus, RecordState, SourceRegistry, UserRole
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


async def test_conditional_get_short_circuits_on_304(monkeypatch):
    """PR 1: When prior ETag is sent and origin returns 304, capture short-circuits with cache_hit=True."""
    captured_headers: dict[str, str] = {}

    class FakeResp:
        status_code = 304
        headers = {"ETag": "W/abc", "Last-Modified": "Wed, 12 May 2026 10:00:00 GMT"}
        text = ""
        url = "https://www.chevening.org/scholarship/pakistan/"

        def raise_for_status(self):
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, headers=None, **kw):
            if headers:
                captured_headers.update(headers)
            return FakeResp()

    monkeypatch.setattr(
        "app.services.ingestion.service.httpx.AsyncClient",
        lambda **kw: FakeClient(),
    )

    svc = IngestionService(db=FakeSession())  # type: ignore[arg-type]
    result = await svc._capture_source_once_with_cache(
        url="https://www.chevening.org/scholarship/pakistan/",
        attempt=1,
        prior_etag="W/abc",
        prior_last_modified="Wed, 12 May 2026 10:00:00 GMT",
    )

    assert result.metadata.get("cache_hit") is True
    assert result.metadata.get("status_code") == 304
    assert captured_headers.get("If-None-Match") == "W/abc"
    assert captured_headers.get("If-Modified-Since") == "Wed, 12 May 2026 10:00:00 GMT"
    assert result.capture_mode == "httpx_cached"
    assert result.html == ""


async def test_conditional_get_returns_full_capture_on_200(monkeypatch):
    """PR 1: When prior ETag mismatches, origin returns 200 with new ETag in metadata."""

    class FakeResp:
        status_code = 200
        headers = {"ETag": "W/new", "Last-Modified": "Thu, 13 May 2026 11:00:00 GMT"}
        text = "<html><head><title>Chevening</title></head><body>fresh</body></html>"
        url = "https://www.chevening.org/scholarship/pakistan/"

        def raise_for_status(self):
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, headers=None, **kw):
            return FakeResp()

    monkeypatch.setattr(
        "app.services.ingestion.service.httpx.AsyncClient",
        lambda **kw: FakeClient(),
    )

    svc = IngestionService(db=FakeSession())  # type: ignore[arg-type]
    result = await svc._capture_source_once_with_cache(
        url="https://www.chevening.org/scholarship/pakistan/",
        attempt=1,
        prior_etag="W/old",
        prior_last_modified=None,
    )

    assert result.metadata.get("cache_hit") is False
    assert result.metadata.get("status_code") == 200
    assert result.metadata.get("etag") == "W/new"
    assert result.metadata.get("last_modified") == "Thu, 13 May 2026 11:00:00 GMT"
    assert result.html.startswith("<html>")
    assert result.capture_mode == "httpx_cached"


# ---------- PR 2: Sitemap + RSS/Atom feed discovery ----------


async def test_discover_urls_from_robots_sitemap(monkeypatch):
    """PR 2: robots.txt Sitemap: directives are followed and in-scope URLs are returned."""

    robots = (
        "User-agent: *\n"
        "Disallow: /admin\n"
        "Sitemap: https://example.gov/sitemap.xml\n"
    )
    sitemap = (
        '<?xml version="1.0"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "  <url><loc>https://example.gov/scholarships/chevening-2027</loc></url>"
        "  <url><loc>https://example.gov/scholarships/fulbright-pk</loc></url>"
        "  <url><loc>https://example.gov/about</loc></url>"
        "</urlset>"
    )

    class FakeResp:
        def __init__(self, text: str, status_code: int = 200):
            self.text = text
            self.status_code = status_code
            self.headers: dict[str, str] = {}

        def raise_for_status(self):
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, headers=None, **kw):
            if url.endswith("robots.txt"):
                return FakeResp(robots)
            if url.endswith("sitemap.xml"):
                return FakeResp(sitemap)
            return FakeResp("", status_code=404)

    monkeypatch.setattr(
        "app.services.ingestion.service.httpx.AsyncClient",
        lambda **kw: FakeClient(),
    )

    svc = IngestionService(db=FakeSession())  # type: ignore[arg-type]
    urls = await svc._discover_source_urls(
        base_url="https://example.gov/",
        scope_keywords=["scholarship", "chevening", "fulbright"],
        try_homepage_feeds=False,
    )

    assert "https://example.gov/scholarships/chevening-2027" in urls
    assert "https://example.gov/scholarships/fulbright-pk" in urls
    assert "https://example.gov/about" not in urls


async def test_discover_urls_from_rss_link_alternate(monkeypatch):
    """PR 2: homepage <link rel='alternate' type='rss+xml'> feeds yield in-scope URLs."""

    homepage = (
        '<html><head>'
        '<link rel="alternate" type="application/rss+xml" href="/feeds/scholarships.rss"/>'
        "</head><body>home</body></html>"
    )
    rss = (
        '<rss version="2.0"><channel>'
        "<item><link>https://example.org/awards/daad-2027</link>"
        "<title>DAAD 2027</title></item>"
        "<item><link>https://example.org/news/conference</link>"
        "<title>Conference</title></item>"
        "</channel></rss>"
    )

    class FakeResp:
        def __init__(self, text: str, status_code: int = 200):
            self.text = text
            self.status_code = status_code
            self.headers: dict[str, str] = {}

        def raise_for_status(self):
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, headers=None, **kw):
            if url.endswith("robots.txt"):
                return FakeResp("", status_code=404)
            if url.endswith("sitemap.xml"):
                return FakeResp("", status_code=404)
            if url.endswith(".rss") or url.endswith(".rss/"):
                return FakeResp(rss)
            return FakeResp(homepage)

    monkeypatch.setattr(
        "app.services.ingestion.service.httpx.AsyncClient",
        lambda **kw: FakeClient(),
    )

    svc = IngestionService(db=FakeSession())  # type: ignore[arg-type]
    urls = await svc._discover_source_urls(
        base_url="https://example.org/",
        scope_keywords=["scholarship", "daad", "award"],
        try_homepage_feeds=True,
    )

    assert "https://example.org/awards/daad-2027" in urls
    assert "https://example.org/news/conference" not in urls


async def test_discover_urls_filters_off_host(monkeypatch):
    """PR 2: discovered URLs must share host with base_url."""

    sitemap = (
        '<?xml version="1.0"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "  <url><loc>https://example.gov/scholarships/x</loc></url>"
        "  <url><loc>https://other.com/scholarships/leak</loc></url>"
        "</urlset>"
    )

    class FakeResp:
        def __init__(self, text: str, status_code: int = 200):
            self.text = text
            self.status_code = status_code
            self.headers: dict[str, str] = {}

        def raise_for_status(self):
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, headers=None, **kw):
            if url.endswith("robots.txt"):
                return FakeResp("", status_code=404)
            if url.endswith("sitemap.xml"):
                return FakeResp(sitemap)
            return FakeResp("", status_code=404)

    monkeypatch.setattr(
        "app.services.ingestion.service.httpx.AsyncClient",
        lambda **kw: FakeClient(),
    )

    svc = IngestionService(db=FakeSession())  # type: ignore[arg-type]
    urls = await svc._discover_source_urls(
        base_url="https://example.gov/",
        scope_keywords=["scholarship"],
        try_homepage_feeds=False,
    )

    assert "https://example.gov/scholarships/x" in urls
    assert "https://other.com/scholarships/leak" not in urls


def _source(source_key: str, display_name: str, base_url: str) -> SourceRegistry:
    source = SourceRegistry(
        source_key=source_key,
        display_name=display_name,
        base_url=base_url,
        source_type="official",
        is_active=True,
    )
    source.id = uuid4()
    source.created_at = datetime.now(timezone.utc)
    source.updated_at = datetime.now(timezone.utc)
    return source


# --- Phase 1: Pakistan-first parser geo flip -------------------------------


async def test_infer_country_code_defaults_to_pakistan():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    source = _source(
        "hec-overseas",
        "HEC Overseas Scholarship Programme",
        "https://www.hec.gov.pk/scholarships",
    )
    assert service._infer_country_code(source, "https://www.hec.gov.pk/scholarships/x") == "PK"


async def test_infer_country_code_detects_destination_countries():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    cases = [
        (_source("chevening", "Chevening Scholarships", "https://www.chevening.org"),
         "https://www.chevening.org/scholarship", "GB"),
        (_source("ukri-studentships", "UKRI", "https://www.ukri.org"),
         "https://www.bristol.ac.uk/funding/award", "GB"),
        (_source("fulbright-foreign", "Fulbright Foreign Student", "https://foreign.fulbrightonline.org"),
         "https://foreign.fulbrightonline.org/apply", "US"),
        (_source("daad-scholarships", "DAAD", "https://www.daad.de"),
         "https://www.daad.de/en/study/scholarship", "DE"),
        (_source("acu-commonwealth", "Commonwealth Scholarships", "https://cscuk.fcdo.gov.uk"),
         "https://study.unimelb.edu.au/scholarship", "AU"),
    ]
    for source, url, expected in cases:
        assert service._infer_country_code(source, url) == expected, (source.source_key, url)


async def test_infer_field_tags_covers_pakistan_breadth():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    assert "engineering" in service._infer_field_tags("Master of Science in Civil Engineering")
    assert "business" in service._infer_field_tags("Fully funded MBA business administration award")
    assert "medicine" in service._infer_field_tags("MPhil public health and medicine scholarship")
    assert "law" in service._infer_field_tags("LLM in international law fellowship")
    assert "social sciences" in service._infer_field_tags("MA in sociology and social sciences")
    assert "computer science" in service._infer_field_tags("MS computer science grant")
    assert "agriculture" in service._infer_field_tags("MSc agriculture and agronomy bursary")
    assert "education" in service._infer_field_tags("Master of Education teaching scholarship")
    # existing entries still match
    assert "data science" in service._infer_field_tags("MS in data science")


async def test_candidate_in_scope_pakistan_sources_without_fulbright():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    chevening = _source("chevening", "Chevening Scholarships", "https://www.chevening.org")
    assert service._candidate_text_in_scope(
        chevening, "Chevening Scholarship 2026 fully funded award for masters study"
    ) is True
    hec = _source("hec-overseas", "HEC Overseas", "https://www.hec.gov.pk")
    # non-scholarship page on a Pakistani source is still rejected
    assert service._candidate_text_in_scope(hec, "About us and contact information") is False


# --- Phase 2: Richer parser extraction -------------------------------------


async def test_parse_candidates_extracts_microdata():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    source = make_source()
    html = """
    <html><body>
      <div itemscope itemtype="https://schema.org/Scholarship">
        <span itemprop="name">Data Science Excellence Scholarship</span>
        <a itemprop="url" href="/awards/data-science-excellence">apply</a>
        <span itemprop="description">Fully funded data science scholarship for masters students</span>
        <span itemprop="applicationDeadline">2026-11-30</span>
      </div>
    </body></html>
    """
    capture = make_capture(html)
    result = service._parse_candidates(source, capture)
    micro = [c for c in result.candidates if c.provenance_payload.get("parse_origin") == "microdata"]
    assert len(micro) == 1
    assert result.diagnostics["microdata_candidates"] == 1
    assert micro[0].title == "Data Science Excellence Scholarship"
    assert str(micro[0].source_url).endswith("/awards/data-science-excellence")


async def test_build_candidate_extracts_structured_deadline():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    source = make_source()
    capture = make_capture("<html></html>")
    c1 = service._build_candidate(
        source=source,
        capture=capture,
        resolved_url="https://uwaterloo.ca/awards/x",
        title="Data Science Scholarship",
        combined_text="Data Science Scholarship fully funded",
        context_text="Data Science Scholarship",
        parse_origin="jsonld",
        structured_hints={"applicationDeadline": "2026-11-30"},
    )
    assert c1 is not None and c1.deadline_at is not None
    assert (c1.deadline_at.year, c1.deadline_at.month, c1.deadline_at.day) == (2026, 11, 30)
    assert c1.to_import_request().deadline_at == c1.deadline_at
    c2 = service._build_candidate(
        source=source,
        capture=capture,
        resolved_url="https://uwaterloo.ca/awards/y",
        title="Data Science Scholarship",
        combined_text="Data Science Scholarship. Application deadline: 1 December 2026.",
        context_text="Data Science Scholarship",
        parse_origin="anchor",
    )
    assert c2 is not None and c2.deadline_at is not None
    assert (c2.deadline_at.year, c2.deadline_at.month, c2.deadline_at.day) == (2026, 12, 1)


async def test_extract_funding_structured_amount():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    pkr = service._extract_funding_structured("Award covers PKR 1,500,000 per year plus tuition")
    assert pkr == {"amount_min": 1500000.0, "amount_max": 1500000.0, "currency": "PKR"}
    gbp = service._extract_funding_structured("£18,000 stipend annually")
    assert gbp is not None and gbp["currency"] == "GBP" and gbp["amount_min"] == 18000.0
    assert service._extract_funding_structured("Funding available for all students") is None
    cand = service._build_candidate(
        source=make_source(),
        capture=make_capture("<html></html>"),
        resolved_url="https://uwaterloo.ca/awards/z",
        title="Data Science Scholarship",
        combined_text="Data Science Scholarship covering PKR 1,500,000 per year",
        context_text="Data Science Scholarship",
        parse_origin="anchor",
    )
    assert cand is not None
    assert cand.provenance_payload.get("funding_structured", {}).get("currency") == "PKR"


# --- Phase 3: dedup, drift, pagination -------------------------------------


def _parsed(title: str, url: str, **overrides) -> "object":
    from app.services.ingestion.service import ParsedScholarshipCandidate

    data = dict(
        source_key="pk-aggregator",
        source_display_name="PK Scholarship Aggregator",
        source_base_url="https://aggregator.pk/",
        source_type="official",
        title=title,
        provider_name="Chevening",
        country_code="GB",
        source_url=url,
    )
    data.update(overrides)
    return ParsedScholarshipCandidate(**data)


async def test_normalize_title_drops_year_and_punctuation():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    assert service._normalize_title("Chevening Scholarship 2026!") == "chevening scholarship"
    assert service._normalize_title("  HEC   Overseas - Phase II  ") == "hec overseas phase ii"


async def test_select_fuzzy_match_finds_near_identical_title():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    candidate = _parsed("Chevening Scholarship 2026", "https://aggregator.pk/new")
    pool = [
        SimpleNamespace(id=uuid4(), title="Commonwealth Split-Site Award",
                        source_url="https://aggregator.pk/b",
                        source_document_ref=None, content_hash=None),
        SimpleNamespace(id=uuid4(), title="Chevening Scholarships 2025",
                        source_url="https://aggregator.pk/c",
                        source_document_ref=None, content_hash=None),
    ]
    match = service._select_fuzzy_match(candidate, pool)
    assert match is not None and match.title == "Chevening Scholarships 2025"
    # no near match -> None
    assert service._select_fuzzy_match(candidate, pool[:1]) is None


async def test_precheck_routes_fuzzy_duplicates_to_review(monkeypatch):
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    candidate = _parsed("Chevening Scholarship 2026", "https://aggregator.pk/new")
    existing = SimpleNamespace(id=uuid4(), title="Chevening Scholarships 2026",
                               source_url="https://aggregator.pk/old",
                               source_document_ref=None, content_hash="h-old")

    async def fake_exact(where_clause):
        return None

    async def fake_fuzzy(cand):
        return existing

    monkeypatch.setattr(service, "_find_existing_scholarship", fake_exact)
    monkeypatch.setattr(service, "_find_fuzzy_duplicate", fake_fuzzy)
    result = await service._precheck_existing_candidates([candidate])

    assert "https://aggregator.pk/new" not in result["skip_matches"]
    advisory = next(a for a in result["advisories"] if a.get("match_type") == "fuzzy_title")
    assert advisory["review_recommended"] is True
    assert result["diagnostics"]["fuzzy_title_matches"] == 1


async def test_snapshot_signature_changes_with_content():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    a = service._snapshot_signature("<html><body>Award A</body></html>")
    b = service._snapshot_signature("<html><body>Award B totally different</body></html>")
    same_whitespace = service._snapshot_signature("<html>  <body>Award A</body>   </html>")
    assert a != b
    assert a == same_whitespace


async def test_detect_snapshot_drift_flags_changed_published_source(monkeypatch):
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    source = make_source()
    run = SimpleNamespace(source_registry=source, source_registry_id=source.id, id=uuid4())
    capture = make_capture("<html><body>NEW funding details changed materially</body></html>")

    async def fake_prior(source_id):
        return "<html><body>OLD funding details</body></html>"

    async def fake_flag(source_id, run_obj):
        return [{"record_id": "r1"}]

    monkeypatch.setattr(service, "_load_prior_snapshot_html", fake_prior)
    monkeypatch.setattr(service, "_flag_source_records_for_revalidation", fake_flag)
    drift = await service._detect_snapshot_drift(run, capture)
    assert drift is not None and drift["detected"] is True
    assert drift["affected_records"] == [{"record_id": "r1"}]

    async def fake_none(source_id):
        return None

    monkeypatch.setattr(service, "_load_prior_snapshot_html", fake_none)
    assert await service._detect_snapshot_drift(run, capture) is None


async def test_pagination_follows_numbered_pages(monkeypatch):
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    pages = {
        "https://x.org/list": '<html><body><a href="?page=2">2</a></body></html>',
        "https://x.org/list?page=2": '<html><body><a href="?page=3">3</a></body></html>',
        "https://x.org/list?page=3": "<html><body>end</body></html>",
    }

    async def fake_capture(url):
        return CaptureResult(html=pages[url], final_url=url, title="t",
                             capture_mode="httpx_fallback", metadata={})

    monkeypatch.setattr(service, "_capture_source", fake_capture)
    results = await service._capture_source_with_pagination("https://x.org/list", max_pages=3)
    assert [r.final_url for r in results] == [
        "https://x.org/list", "https://x.org/list?page=2", "https://x.org/list?page=3",
    ]


async def test_pagination_follows_load_more(monkeypatch):
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    pages = {
        "https://x.org/list": '<html><body><button class="load-more" data-url="/list?p=2">Load more</button></body></html>',
        "https://x.org/list?p=2": "<html><body>done</body></html>",
    }

    async def fake_capture(url):
        return CaptureResult(html=pages[url], final_url=url, title="t",
                             capture_mode="httpx_fallback", metadata={})

    monkeypatch.setattr(service, "_capture_source", fake_capture)
    results = await service._capture_source_with_pagination("https://x.org/list", max_pages=3)
    assert [r.final_url for r in results] == ["https://x.org/list", "https://x.org/list?p=2"]


# --- Phase 4: diagnostics filter + provenance trace ------------------------


async def test_list_runs_filters_by_parser_diagnostic():
    session = FakeSession()
    service = IngestionService(session)
    source_one = make_source()
    source_two = make_source()
    source_two.source_key = "fulbright-foreign-student"

    run_a = IngestionRun(
        id=uuid4(), source_registry=source_one, source_registry_id=source_one.id,
        triggered_by_user_id=uuid4(), institution_id=None,
        status=IngestionRunStatus.PARTIAL, fetch_url=str(source_one.base_url),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        run_metadata={"parser": {"fallback_used": True}},
    )
    run_b = IngestionRun(
        id=uuid4(), source_registry=source_two, source_registry_id=source_two.id,
        triggered_by_user_id=uuid4(), institution_id=None,
        status=IngestionRunStatus.COMPLETED, fetch_url=str(source_two.base_url),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        run_metadata={"parser": {"fallback_used": False, "microdata_candidates": 2}},
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
        parser_diagnostic="fallback_used",
    )
    assert filtered.total == 1
    assert filtered.items[0].source_key == source_one.source_key

    micro = await service.list_runs(
        actor_user=SimpleNamespace(id=uuid4(), role=UserRole.ADMIN, institution_id=None),
        parser_diagnostic="microdata_candidates",
    )
    assert micro.total == 1
    assert micro.items[0].source_key == "fulbright-foreign-student"


async def test_trace_provenance_returns_lineage(monkeypatch):
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    source = make_source()
    scholarship = SimpleNamespace(
        id=uuid4(), record_state=RecordState.PUBLISHED,
        source_url="https://uwaterloo.ca/awards/x", content_hash="hash-1",
        source_document_ref="x", imported_at=None,
        provenance_payload={"parse_origin": "microdata"},
        source_registry=source, source_registry_id=source.id,
    )
    run = SimpleNamespace(id=uuid4(), capture_mode="playwright")

    async def fake_load(sid):
        return scholarship

    async def fake_run(sch):
        return run

    monkeypatch.setattr(service, "_load_scholarship_for_provenance", fake_load)
    monkeypatch.setattr(service, "_find_originating_run", fake_run)

    resp = await service.trace_provenance(scholarship.id)
    assert resp.source_key == source.source_key
    assert resp.originating_run_id == str(run.id)
    assert resp.capture_mode == "playwright"
    assert resp.record_state == "published"
    assert resp.provenance_payload == {"parse_origin": "microdata"}


async def test_trace_provenance_404_for_unpublished_or_missing(monkeypatch):
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    raw = SimpleNamespace(
        id=uuid4(), record_state=RecordState.RAW,
        source_url="https://uwaterloo.ca/awards/y", content_hash=None,
        source_document_ref=None, imported_at=None, provenance_payload=None,
        source_registry=None, source_registry_id=None,
    )

    async def fake_load_raw(sid):
        return raw

    monkeypatch.setattr(service, "_load_scholarship_for_provenance", fake_load_raw)
    with pytest.raises(HTTPException) as exc:
        await service.trace_provenance(raw.id)
    assert exc.value.status_code == 404

    async def fake_load_none(sid):
        return None

    monkeypatch.setattr(service, "_load_scholarship_for_provenance", fake_load_none)
    with pytest.raises(HTTPException) as exc2:
        await service.trace_provenance(uuid4())
    assert exc2.value.status_code == 404


# --- Phase 5: infra hardening (async / source-health) ----------------------


async def test_resolve_execution_mode_routes_large_auto_jobs_to_worker():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    big = IngestionRunStartRequest(source_key="hec-overseas", max_records=20, execution_mode="auto")
    small = IngestionRunStartRequest(source_key="hec-overseas", max_records=5, execution_mode="auto")
    assert service._resolve_execution_mode(big) == "worker"
    assert service._resolve_execution_mode(small) == "inline"
    assert service._resolve_execution_mode(
        IngestionRunStartRequest(source_key="hec-overseas", max_records=20, execution_mode="inline")
    ) == "inline"
    assert service._resolve_execution_mode(
        IngestionRunStartRequest(source_key="hec-overseas", max_records=2, execution_mode="worker")
    ) == "worker"


async def test_classify_source_health_thresholds():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    assert service._classify_source_health(0) == "healthy"
    assert service._classify_source_health(2) == "healthy"
    assert service._classify_source_health(3) == "degraded"
    assert service._classify_source_health(5) == "degraded"
    assert service._classify_source_health(6) == "down"


async def test_record_source_health_updates_counters():
    service = IngestionService(FakeSession())  # type: ignore[arg-type]
    source = make_source()
    for _ in range(3):
        service._record_source_health(source, success=False)
    assert source.consecutive_failures == 3
    assert source.health_status == "degraded"
    assert source.last_failure_at is not None

    service._record_source_health(source, success=True)
    assert source.consecutive_failures == 0
    assert source.health_status == "healthy"
    assert source.last_success_at is not None


async def test_list_source_health_returns_per_source_rows():
    session = FakeSession()
    service = IngestionService(session)
    source_a = make_source()
    source_a.health_status = "healthy"
    source_a.consecutive_failures = 0
    source_b = make_source()
    source_b.source_key = "chevening"
    source_b.health_status = "down"
    source_b.consecutive_failures = 7

    class ListResult:
        def __init__(self, rows):
            self._rows = rows

        def scalars(self):
            return SimpleNamespace(all=lambda: self._rows)

    async def fake_execute(_query):
        return ListResult([source_a, source_b])

    session.execute = fake_execute
    response = await service.list_source_health(
        actor_user=SimpleNamespace(id=uuid4(), role=UserRole.ADMIN, institution_id=None)
    )
    assert response.total == 2
    by_key = {item.source_key: item for item in response.items}
    assert by_key["chevening"].health_status == "down"
    assert by_key["chevening"].consecutive_failures == 7
