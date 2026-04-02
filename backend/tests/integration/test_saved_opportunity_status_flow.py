from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import Application, ApplicationStatus, RecordState, UserRole


class _ScalarCollection:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _ExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _ScalarCollection(self._items)

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


class _FakeDB:
    def __init__(self, application: Application):
        self.application = application
        self.execute_calls = 0
        self.committed = False

    async def execute(self, _query):
        self.execute_calls += 1
        if self.execute_calls == 1:
            return _ExecuteResult([self.application])
        return _ExecuteResult([self.application])

    async def flush(self):
        return None

    async def refresh(self, _value):
        return None

    async def commit(self):
        self.committed = True
        return None


def _build_application(status: ApplicationStatus) -> Application:
    scholarship_id = uuid4()
    scholarship = SimpleNamespace(
        id=scholarship_id,
        title="Scholarship Tracker Target",
        provider_name="Provider",
        country_code="CA",
        deadline_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        record_state=RecordState.PUBLISHED,
        source_url="https://example.com/scholarship",
        summary="Summary",
    )
    application = Application(
        user_id=uuid4(),
        scholarship_id=scholarship_id,
        status=status,
    )
    application.id = uuid4()
    application.created_at = datetime.now(timezone.utc)
    application.updated_at = datetime.now(timezone.utc)
    application.scholarship = scholarship
    return application


def _fake_user(capabilities: set[str]):
    return SimpleNamespace(
        id=uuid4(),
        role=UserRole.STUDENT,
        is_active=True,
        _token_capabilities=capabilities,
    )


def test_saved_opportunity_status_update_requires_authentication(client):
    response = client.patch(
        f"/api/v1/saved-opportunities/{uuid4()}/status",
        json={"status": "applied"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_saved_opportunity_status_update_updates_tracker(app, client):
    application = _build_application(ApplicationStatus.SAVED)
    db = _FakeDB(application)

    async def override_current_user():
        return _fake_user({"saved_opportunity.self.write"})

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.patch(
        f"/api/v1/saved-opportunities/{application.scholarship_id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["scholarship_id"] == str(application.scholarship_id)
    assert payload["tracker_status"] == "in_progress"
    assert payload["record_state"] == "published"


def test_saved_opportunity_list_surfaces_tracker_status(app, client):
    application = _build_application(ApplicationStatus.SUBMITTED)
    db = _FakeDB(application)

    async def override_current_user():
        return _fake_user({"saved_opportunity.self.read"})

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/api/v1/saved-opportunities",
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["tracker_status"] == "applied"
