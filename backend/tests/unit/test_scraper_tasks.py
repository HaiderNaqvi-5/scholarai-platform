from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

pytest.importorskip("celery")

from app.tasks import scraper_tasks


class FakeDetail:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self):
        return self.payload


class _FakeScalarResult:
    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return self._items


class _FakeExecuteResult:
    def __init__(self, items):
        self._items = list(items)

    def scalars(self):
        return _FakeScalarResult(self._items)

    def first(self):
        return self._items[0] if self._items else None


class FakeSession:
    def __init__(self, sources=None):
        self.commits = 0
        self._sources = list(sources or [])

    async def commit(self):
        self.commits += 1

    async def execute(self, _stmt):
        return _FakeExecuteResult(self._sources)


class FakeSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_run_payload(run_id: str) -> dict:
    return {
        "run_id": run_id,
        "source_key": "waterloo-awards",
        "source_display_name": "University of Waterloo Graduate Funding",
        "fetch_url": "https://uwaterloo.ca/graduate-studies-postdoctoral-affairs/funding",
        "status": "partial",
        "capture_mode": "httpx_fallback",
        "parser_name": "official_page_parser_v3",
        "records_found": 2,
        "records_created": 1,
        "records_skipped": 1,
        "failure_reason": None,
        "started_at": None,
        "completed_at": None,
        "created_at": "2026-03-20T00:00:00+00:00",
        "run_metadata": {
            "execution": {
                "requested_mode": "worker",
                "selected_mode": "worker",
                "dispatch_status": "running",
                "celery_task_id": "celery-123",
            }
        },
    }


def test_run_source_ingestion_executes_existing_run_when_run_id_provided(monkeypatch):
    session = FakeSession()
    captured = {}

    class FakeIngestionService:
        def __init__(self, db):
            captured["db"] = db

        async def execute_run(
            self,
            run_id,
            *,
            actor_user_id,
            max_records,
            execution_context,
            persist_running_state,
        ):
            captured["execute"] = {
                "run_id": run_id,
                "actor_user_id": actor_user_id,
                "max_records": max_records,
                "execution_context": execution_context,
                "persist_running_state": persist_running_state,
            }
            payload = make_run_payload(str(run_id))
            return FakeDetail(payload)

    monkeypatch.setattr(
        scraper_tasks,
        "async_session_factory",
        lambda: FakeSessionContext(session),
    )
    monkeypatch.setattr(scraper_tasks, "IngestionService", FakeIngestionService)

    run_id = str(uuid4())
    result = scraper_tasks.run_source_ingestion(run_id=run_id, max_records=7)

    assert captured["db"] is session
    assert captured["execute"]["run_id"] == UUID(run_id)
    assert captured["execute"]["actor_user_id"] is None
    assert captured["execute"]["max_records"] == 7
    assert captured["execute"]["execution_context"] == {
        "selected_mode": "worker",
        "dispatch_status": "running",
    }
    assert captured["execute"]["persist_running_state"] is True
    assert result["run_id"] == run_id
    assert result["execution_mode_selected"] == "worker"
    assert result["dispatch_status"] == "running"
    assert result["celery_task_id"] == "celery-123"
    assert session.commits == 1


def test_run_source_ingestion_creates_and_executes_worker_run(monkeypatch):
    session = FakeSession()
    captured = {}
    created_run_id = str(uuid4())

    class FakeIngestionService:
        def __init__(self, db):
            captured["db"] = db

        async def create_run(self, payload, actor_user_id):
            captured["create"] = {
                "payload": payload,
                "actor_user_id": actor_user_id,
            }
            return SimpleNamespace(run_id=created_run_id)

        async def execute_run(
            self,
            run_id,
            *,
            actor_user_id,
            max_records,
            execution_context,
            persist_running_state,
        ):
            captured["execute"] = {
                "run_id": run_id,
                "actor_user_id": actor_user_id,
                "max_records": max_records,
                "execution_context": execution_context,
                "persist_running_state": persist_running_state,
            }
            payload = make_run_payload(str(run_id))
            return FakeDetail(payload)

    monkeypatch.setattr(
        scraper_tasks,
        "async_session_factory",
        lambda: FakeSessionContext(session),
    )
    monkeypatch.setattr(scraper_tasks, "IngestionService", FakeIngestionService)

    actor_user_id = str(uuid4())
    result = scraper_tasks.run_source_ingestion(
        source_key="waterloo-awards",
        actor_user_id=actor_user_id,
        source_display_name="University of Waterloo Graduate Funding",
        source_base_url="https://uwaterloo.ca/graduate-studies-postdoctoral-affairs/funding",
        source_type="official",
        max_records=3,
    )

    assert captured["db"] is session
    assert captured["create"]["actor_user_id"] == UUID(actor_user_id)
    assert captured["create"]["payload"].source_key == "waterloo-awards"
    assert captured["create"]["payload"].execution_mode == "worker"
    assert captured["execute"]["run_id"] == UUID(created_run_id)
    assert captured["execute"]["actor_user_id"] == UUID(actor_user_id)
    assert captured["execute"]["max_records"] == 3
    assert captured["execute"]["execution_context"] == {
        "requested_mode": "worker",
        "selected_mode": "worker",
        "dispatch_status": "running",
    }
    assert captured["execute"]["persist_running_state"] is True
    assert result["run_id"] == created_run_id
    assert result["execution_mode_selected"] == "worker"
    assert session.commits == 1


def test_run_source_ingestion_falls_back_to_start_run_for_legacy_service(monkeypatch):
    session = FakeSession()
    captured = {}

    class FakeIngestionService:
        def __init__(self, db):
            captured["db"] = db

        async def start_run(self, payload, actor_user_id):
            captured["start_run"] = {
                "payload": payload,
                "actor_user_id": actor_user_id,
            }
            return FakeDetail(make_run_payload(str(uuid4())))

    monkeypatch.setattr(
        scraper_tasks,
        "async_session_factory",
        lambda: FakeSessionContext(session),
    )
    monkeypatch.setattr(scraper_tasks, "IngestionService", FakeIngestionService)

    actor_user_id = str(uuid4())
    result = scraper_tasks.run_source_ingestion(
        source_key="waterloo-awards",
        actor_user_id=actor_user_id,
        source_display_name="University of Waterloo Graduate Funding",
        source_base_url="https://uwaterloo.ca/graduate-studies-postdoctoral-affairs/funding",
        source_type="official",
        max_records=3,
    )

    assert captured["db"] is session
    assert captured["start_run"]["actor_user_id"] == UUID(actor_user_id)
    assert captured["start_run"]["payload"].execution_mode == "worker"
    assert result["execution_mode_selected"] == "worker"
    assert session.commits == 1


def test_run_nightly_ingestion_uses_reserved_system_identity(monkeypatch):
    session = FakeSession()
    captured = {}
    created_run_id = str(uuid4())

    class FakeIngestionService:
        def __init__(self, db):
            captured["db"] = db

        async def create_run(self, payload, actor_user_id):
            captured["create"] = {
                "payload": payload,
                "actor_user_id": actor_user_id,
            }
            return SimpleNamespace(run_id=created_run_id)

        async def execute_run(
            self,
            run_id,
            *,
            actor_user_id,
            max_records,
            execution_context,
            persist_running_state,
        ):
            captured["execute"] = {
                "run_id": run_id,
                "actor_user_id": actor_user_id,
                "max_records": max_records,
                "execution_context": execution_context,
                "persist_running_state": persist_running_state,
            }
            return FakeDetail(make_run_payload(str(run_id)))

    monkeypatch.setattr(
        scraper_tasks,
        "async_session_factory",
        lambda: FakeSessionContext(session),
    )
    monkeypatch.setattr(scraper_tasks, "IngestionService", FakeIngestionService)

    result = scraper_tasks.run_nightly_ingestion()

    assert captured["db"] is session
    assert captured["create"]["payload"].source_key == "nightly_sync_main"
    assert captured["create"]["payload"].source_display_name == "Auto Nightly Ingestion"
    assert captured["create"]["payload"].source_base_url is None
    assert captured["create"]["payload"].source_type == "official"
    assert captured["create"]["payload"].max_records == 20
    assert captured["create"]["payload"].execution_mode == "worker"
    assert captured["create"]["actor_user_id"] == UUID("00000000-0000-0000-0000-000000000000")
    assert captured["execute"]["run_id"] == UUID(created_run_id)
    assert captured["execute"]["max_records"] == 20
    assert result["run_id"] == created_run_id
    assert session.commits == 1


# --- Phase 5: nightly automation hardening ---------------------------------


def test_nightly_run_is_stale():
    from datetime import datetime, timedelta, timezone

    now = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
    fresh = now - timedelta(hours=3)
    stale = now - timedelta(hours=30)
    assert scraper_tasks._nightly_run_is_stale(None, now=now) is True
    assert scraper_tasks._nightly_run_is_stale(fresh, now=now) is False
    assert scraper_tasks._nightly_run_is_stale(stale, now=now) is True


def test_should_run_nightly_skips_when_recent(monkeypatch):
    import asyncio
    from datetime import datetime, timedelta, timezone

    recent = datetime.now(timezone.utc) - timedelta(hours=2)

    async def fake_last(_session):
        return recent

    monkeypatch.setattr(scraper_tasks, "_load_last_nightly_completion", fake_last)
    assert asyncio.run(scraper_tasks._should_run_nightly(object())) is False


def test_should_run_nightly_runs_when_stale_or_never(monkeypatch):
    import asyncio
    from datetime import datetime, timedelta, timezone

    stale = datetime.now(timezone.utc) - timedelta(hours=40)

    async def fake_stale(_session):
        return stale

    async def fake_never(_session):
        return None

    monkeypatch.setattr(scraper_tasks, "_load_last_nightly_completion", fake_stale)
    assert asyncio.run(scraper_tasks._should_run_nightly(object())) is True
    monkeypatch.setattr(scraper_tasks, "_load_last_nightly_completion", fake_never)
    assert asyncio.run(scraper_tasks._should_run_nightly(object())) is True


# --- Phase 6: staggered fan-out + health check -----------------------------


def test_run_nightly_dispatches_one_task_per_active_source(monkeypatch):
    """Active SourceRegistry rows fan out via apply_async with increasing countdown."""
    sources = [
        SimpleNamespace(
            source_key="chevening",
            display_name="Chevening",
            base_url="https://chevening.org",
            source_type="official",
        ),
        SimpleNamespace(
            source_key="fulbright",
            display_name="Fulbright",
            base_url="https://fulbright.org",
            source_type="official",
        ),
        SimpleNamespace(
            source_key="daad",
            display_name="DAAD",
            base_url="https://daad.de",
            source_type="official",
        ),
    ]
    session = FakeSession(sources=sources)

    async def fake_recent(_session):
        from datetime import datetime, timedelta, timezone
        return datetime.now(timezone.utc) - timedelta(hours=40)

    monkeypatch.setattr(scraper_tasks, "_load_last_nightly_completion", fake_recent)
    monkeypatch.setattr(
        scraper_tasks, "async_session_factory", lambda: FakeSessionContext(session)
    )
    monkeypatch.setattr(scraper_tasks.settings, "INGESTION_STAGGER_SECONDS", 300)

    dispatched: list[dict] = []

    def fake_apply_async(*, kwargs, countdown):
        dispatched.append({"kwargs": kwargs, "countdown": countdown})

    monkeypatch.setattr(
        scraper_tasks.run_source_ingestion, "apply_async", fake_apply_async
    )

    result = scraper_tasks.run_nightly_ingestion()

    assert result["status"] == "dispatched"
    assert result["count"] == 3
    assert result["stagger_seconds"] == 300
    assert [d["countdown"] for d in dispatched] == [0, 300, 600]
    assert [d["kwargs"]["source_key"] for d in dispatched] == [
        "chevening",
        "fulbright",
        "daad",
    ]


def test_run_nightly_falls_back_to_legacy_when_no_active_sources(monkeypatch):
    """Empty SourceRegistry list keeps the legacy nightly_sync_main path firing."""
    session = FakeSession(sources=[])
    captured = {}
    created_run_id = str(uuid4())

    class FakeIngestionService:
        def __init__(self, db):
            captured["db"] = db

        async def create_run(self, payload, actor_user_id):
            captured["create_payload"] = payload
            return SimpleNamespace(run_id=created_run_id)

        async def execute_run(self, run_id, **_kwargs):
            return FakeDetail(make_run_payload(str(run_id)))

    async def fake_stale(_session):
        return None

    monkeypatch.setattr(scraper_tasks, "_load_last_nightly_completion", fake_stale)
    monkeypatch.setattr(
        scraper_tasks, "async_session_factory", lambda: FakeSessionContext(session)
    )
    monkeypatch.setattr(scraper_tasks, "IngestionService", FakeIngestionService)

    result = scraper_tasks.run_nightly_ingestion()

    assert captured["create_payload"].source_key == "nightly_sync_main"
    assert result["run_id"] == created_run_id


def test_ingestion_health_check_alerts_when_stale(monkeypatch):
    """Stale completion triggers logger.error + Sentry capture + admin email."""
    from datetime import datetime, timedelta, timezone

    stale = datetime.now(timezone.utc) - timedelta(hours=48)

    async def fake_last(_session):
        return stale

    monkeypatch.setattr(scraper_tasks, "_load_last_nightly_completion", fake_last)
    monkeypatch.setattr(
        scraper_tasks, "async_session_factory", lambda: FakeSessionContext(FakeSession())
    )
    monkeypatch.setattr(scraper_tasks.settings, "INGESTION_STALE_HOURS", 26)
    monkeypatch.setattr(
        scraper_tasks.settings, "ADMIN_ALERT_EMAIL", "ops@example.com"
    )
    monkeypatch.setattr(scraper_tasks.settings, "SENTRY_DSN", None)

    sent = {}

    async def fake_send_email(user, message, *, subject=None, html=None):
        sent["to"] = user.email
        sent["subject"] = subject
        sent["body"] = message
        return True

    monkeypatch.setattr(scraper_tasks, "send_email", fake_send_email)

    result = scraper_tasks.run_ingestion_health_check()

    assert result["status"] == "stale"
    assert result["hours_since"] is not None and result["hours_since"] > 26
    assert sent["to"] == "ops@example.com"
    assert "Nightly ingestion stale" in sent["subject"]


def test_ingestion_health_check_quiet_when_fresh(monkeypatch):
    """Fresh completion = status='ok' and no email."""
    from datetime import datetime, timedelta, timezone

    fresh = datetime.now(timezone.utc) - timedelta(hours=4)

    async def fake_last(_session):
        return fresh

    monkeypatch.setattr(scraper_tasks, "_load_last_nightly_completion", fake_last)
    monkeypatch.setattr(
        scraper_tasks, "async_session_factory", lambda: FakeSessionContext(FakeSession())
    )
    monkeypatch.setattr(scraper_tasks.settings, "INGESTION_STALE_HOURS", 26)
    monkeypatch.setattr(
        scraper_tasks.settings, "ADMIN_ALERT_EMAIL", "ops@example.com"
    )

    called = {"count": 0}

    async def fake_send_email(*_a, **_k):
        called["count"] += 1
        return True

    monkeypatch.setattr(scraper_tasks, "send_email", fake_send_email)

    result = scraper_tasks.run_ingestion_health_check()

    assert result["status"] == "ok"
    assert called["count"] == 0
