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


class FakeSession:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


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
