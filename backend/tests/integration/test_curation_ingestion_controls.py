from datetime import datetime, timezone
from uuid import uuid4

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import IngestionRunStatus, UserRole
from app.services.ingestion import IngestionService


class _DummyCurrentUser:
    def __init__(self):
        self.id = uuid4()
        self.role = UserRole.ADMIN
        self._token_capabilities = {
            "curation.queue.read",
            "admin.ingestion.run",
        }


class _NoOpDB:
    async def execute(self, _query):
        return None

    def add(self, _value):
        return None

    async def flush(self):
        return None

    async def commit(self):
        return None


def _run_detail_payload(run_id: str, *, status: str, source_key: str, dispatch_status: str):
    now = datetime.now(timezone.utc)
    return {
        "run_id": run_id,
        "source_key": source_key,
        "source_display_name": source_key,
        "fetch_url": "https://example.test/source",
        "status": status,
        "capture_mode": "httpx_fallback",
        "parser_name": "official_page_parser_v3",
        "records_found": 3,
        "records_created": 2,
        "records_skipped": 1,
        "failure_reason": None,
        "started_at": now,
        "completed_at": now,
        "created_at": now,
        "execution_mode_requested": "worker",
        "execution_mode_selected": "inline",
        "dispatch_status": dispatch_status,
        "celery_task_id": "celery-xyz",
        "attempt_count": 2,
        "run_retry_count": 1,
        "last_started_at": now.isoformat(),
        "last_retry_requested_at": now.isoformat(),
        "failure_phase": None,
        "run_metadata": {
            "execution": {
                "requested_mode": "worker",
                "selected_mode": "inline",
                "dispatch_status": dispatch_status,
                "celery_task_id": "celery-xyz",
                "attempt_count": 2,
                "run_retry_count": 1,
                "last_started_at": now.isoformat(),
                "last_retry_requested_at": now.isoformat(),
            }
        },
    }


def test_curation_ingestion_list_supports_filters(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    class FakeIngestionService:
        def __init__(self, _db):
            self._detail = _run_detail_payload(
                str(uuid4()),
                status=IngestionRunStatus.FAILED.value,
                source_key="fulbright-foreign-student",
                dispatch_status="retry_inline",
            )

        async def list_runs(
            self,
            _actor_user,
            *,
            page=1,
            page_size=20,
            status_filter=None,
            source_key=None,
            dispatch_status=None,
        ):
            assert page == 1
            assert page_size == 8
            assert status_filter == "failed"
            assert source_key == "fulbright-foreign-student"
            assert dispatch_status == "retry_inline"
            from app.schemas.curation import IngestionRunListResponse

            item = {
                key: value
                for key, value in self._detail.items()
                if key != "run_metadata"
            }
            return IngestionRunListResponse(items=[item], total=1, page=1, page_size=8, has_more=False)

        async def get_run(self, run_id, actor_user=None):
            assert str(run_id) == self._detail["run_id"]
            assert actor_user is not None
            from app.schemas.curation import IngestionRunDetail

            return IngestionRunDetail(**self._detail)

    original_service = IngestionService
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    import app.api.v1.routes.curation as curation_routes

    curation_routes.IngestionService = FakeIngestionService  # type: ignore[assignment]

    try:
        response = client.get(
            "/api/v1/curation/ingestion-runs?page=1&page_size=8&status=failed&source_key=fulbright-foreign-student&dispatch_status=retry_inline",
            headers={"Authorization": "Bearer fake"},
        )
    finally:
        curation_routes.IngestionService = original_service  # type: ignore[assignment]
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["status"] == "failed"
    assert payload["items"][0]["source_key"] == "fulbright-foreign-student"
    assert payload["items"][0]["dispatch_status"] == "retry_inline"


def test_curation_ingestion_retry_endpoint_returns_detail(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    run_id = str(uuid4())

    class FakeIngestionService:
        def __init__(self, _db):
            self._detail = _run_detail_payload(
                run_id,
                status=IngestionRunStatus.PARTIAL.value,
                source_key="waterloo-awards",
                dispatch_status="retry_inline",
            )

        async def retry_run(self, run_id, *, payload, actor_user):
            assert str(run_id) == self._detail["run_id"]
            assert payload.max_records == 4
            assert payload.execution_mode == "inline"
            assert actor_user.id is not None
            from app.schemas.curation import IngestionRunDetail

            return IngestionRunDetail(**self._detail)

    original_service = IngestionService
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    import app.api.v1.routes.curation as curation_routes

    curation_routes.IngestionService = FakeIngestionService  # type: ignore[assignment]
    try:
        response = client.post(
            f"/api/v1/curation/ingestion-runs/{run_id}/retry",
            json={"max_records": 4, "execution_mode": "inline"},
            headers={"Authorization": "Bearer fake"},
        )
    finally:
        curation_routes.IngestionService = original_service  # type: ignore[assignment]
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["dispatch_status"] == "retry_inline"
    assert payload["run_retry_count"] == 1


def test_curation_ingestion_assign_queue_endpoint_returns_detail(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    run_id = str(uuid4())

    class FakeIngestionService:
        def __init__(self, _db):
            self._detail = _run_detail_payload(
                run_id,
                status=IngestionRunStatus.PARTIAL.value,
                source_key="waterloo-awards",
                dispatch_status="retry_inline",
            )
            self._detail["run_metadata"]["execution"]["review_queue"] = "manual-review"
            self._detail["run_metadata"]["execution"]["queue_assigned_by_user_id"] = str(uuid4())
            self._detail["run_metadata"]["execution"]["queue_assigned_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            self._detail["run_metadata"]["execution"]["queue_assignment_note"] = "priority"

        async def assign_review_queue(self, run_id, *, payload, actor_user):
            assert str(run_id) == self._detail["run_id"]
            assert payload.queue_key == "manual-review"
            assert payload.note == "priority"
            assert actor_user.id is not None
            from app.schemas.curation import IngestionRunDetail

            return IngestionRunDetail(**self._detail)

    original_service = IngestionService
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    import app.api.v1.routes.curation as curation_routes

    curation_routes.IngestionService = FakeIngestionService  # type: ignore[assignment]
    try:
        response = client.post(
            f"/api/v1/curation/ingestion-runs/{run_id}/assign-queue",
            json={"queue_key": "manual-review", "note": "priority"},
            headers={"Authorization": "Bearer fake"},
        )
    finally:
        curation_routes.IngestionService = original_service  # type: ignore[assignment]
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["review_queue"] == "manual-review"
    assert payload["queue_assignment_note"] == "priority"


def test_curation_ingestion_bulk_retry_endpoint_returns_counts(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _NoOpDB()

    run_ok = str(uuid4())
    run_skip = str(uuid4())

    class FakeIngestionService:
        def __init__(self, _db):
            self._detail = _run_detail_payload(
                run_ok,
                status=IngestionRunStatus.PARTIAL.value,
                source_key="waterloo-awards",
                dispatch_status="retry_inline",
            )

        async def bulk_retry_runs(self, *, payload, actor_user):
            assert payload.run_ids == [run_ok, run_skip]
            assert payload.max_records == 4
            assert payload.execution_mode == "inline"
            assert actor_user.id is not None
            from app.schemas.curation import (
                IngestionRunBulkRetryItem,
                IngestionRunBulkRetryResponse,
                IngestionRunDetail,
            )

            detail = IngestionRunDetail(**self._detail)
            return IngestionRunBulkRetryResponse(
                items=[
                    IngestionRunBulkRetryItem(
                        run_id=run_ok,
                        status="retried",
                        message="Run retried successfully",
                        detail=detail,
                    ),
                    IngestionRunBulkRetryItem(
                        run_id=run_skip,
                        status="skipped",
                        message="already running",
                        detail=None,
                    ),
                ],
                total=2,
                retried=1,
                skipped=1,
                failed=0,
            )

    original_service = IngestionService
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    import app.api.v1.routes.curation as curation_routes

    curation_routes.IngestionService = FakeIngestionService  # type: ignore[assignment]
    try:
        response = client.post(
            "/api/v1/curation/ingestion-runs/bulk-retry",
            json={"run_ids": [run_ok, run_skip], "max_records": 4, "execution_mode": "inline"},
            headers={"Authorization": "Bearer fake"},
        )
    finally:
        curation_routes.IngestionService = original_service  # type: ignore[assignment]
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["retried"] == 1
    assert payload["skipped"] == 1
    assert payload["failed"] == 0
