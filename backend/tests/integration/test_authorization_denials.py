import uuid
from types import SimpleNamespace

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole


def _fake_user(*, capabilities: set[str]):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="rbac@example.com",
        full_name="RBAC Test",
        role=UserRole.ADMIN,
        is_active=True,
        _token_capabilities=capabilities,
    )


def test_auth_me_requires_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_auth_me_returns_403_for_missing_session_capability(app, client):
    async def override_current_user():
        return _fake_user(capabilities={"profile.self.read"})

    app.dependency_overrides[get_current_user] = override_current_user
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fake"})

    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "auth_insufficient_permissions"


def test_curation_records_requires_token(client):
    response = client.get("/api/v1/curation/records")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_curation_records_returns_403_for_missing_curation_capability(app, client):
    async def override_current_user():
        return _fake_user(capabilities={"profile.self.read"})

    async def override_db():
        yield object()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.get("/api/v1/curation/records", headers={"Authorization": "Bearer fake"})

    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "auth_insufficient_permissions"


def test_interview_coaching_analytics_returns_403_without_interview_read_capability(app, client):
    async def override_current_user():
        return _fake_user(capabilities={"interview.self.create"})

    async def override_db():
        yield object()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/api/v1/interviews/coaching-analytics",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "auth_insufficient_permissions"
