import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole
from app.schemas.access_control import (
    AccessControlManagedUser,
    AccessControlManagedUserListResponse,
    AccessControlRoleChangeItem,
    AccessControlRoleChangeListResponse,
)


def _fake_user(*, capabilities: set[str]):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="ops@example.com",
        full_name="Ops User",
        role=UserRole.OWNER,
        is_active=True,
        _token_capabilities=capabilities,
    )


def test_access_control_routes_require_authentication(client):
    list_users_response = client.get("/api/v1/access-control/users")
    list_changes_response = client.get("/api/v1/access-control/role-changes")
    update_response = client.patch(
        f"/api/v1/access-control/users/{uuid.uuid4()}/role",
        json={"role": "mentor"},
    )
    revert_response = client.post(
        f"/api/v1/access-control/role-changes/{uuid.uuid4()}/revert",
        json={},
    )

    for response in [
        list_users_response,
        list_changes_response,
        update_response,
        revert_response,
    ]:
        assert response.status_code == 401
        body = response.json()
        assert body["error"]["code"] == "UNAUTHORIZED"


def test_access_control_routes_return_403_for_missing_capabilities(app, client):
    async def override_current_user():
        return _fake_user(capabilities={"profile.self.read"})

    async def override_db():
        yield object()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    list_users_response = client.get(
        "/api/v1/access-control/users",
        headers={"Authorization": "Bearer fake"},
    )
    list_changes_response = client.get(
        "/api/v1/access-control/role-changes",
        headers={"Authorization": "Bearer fake"},
    )
    update_response = client.patch(
        f"/api/v1/access-control/users/{uuid.uuid4()}/role",
        json={"role": "mentor"},
        headers={"Authorization": "Bearer fake"},
    )
    revert_response = client.post(
        f"/api/v1/access-control/role-changes/{uuid.uuid4()}/revert",
        json={},
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert list_users_response.status_code == 403
    assert list_changes_response.status_code == 403
    assert update_response.status_code == 403
    assert revert_response.status_code == 403
    assert list_users_response.json()["error"]["code"] == "auth_insufficient_permissions"
    assert list_changes_response.json()["error"]["code"] == "auth_insufficient_permissions"
    assert update_response.json()["error"]["code"] == "auth_insufficient_permissions"
    assert revert_response.json()["error"]["code"] == "auth_insufficient_permissions"


def test_access_control_routes_list_users_success(app, client):
    async def override_current_user():
        return _fake_user(capabilities={"admin.audit.read"})

    async def override_db():
        yield object()

    managed_user = AccessControlManagedUser(
        user_id=uuid.uuid4(),
        email="student@example.com",
        full_name="Student User",
        role=UserRole.STUDENT,
        is_active=True,
        auth_token_version=2,
        effective_capabilities=["profile.self.read"],
    )

    class FakeAccessControlService:
        def __init__(self, _db):
            pass

        async def list_managed_users(self):
            return AccessControlManagedUserListResponse(items=[managed_user], total=1)

    import app.api.v1.routes.access_control as access_control_routes

    original_service = access_control_routes.AccessControlService
    access_control_routes.AccessControlService = FakeAccessControlService  # type: ignore[assignment]
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/api/v1/access-control/users",
        headers={"Authorization": "Bearer fake"},
    )

    access_control_routes.AccessControlService = original_service  # type: ignore[assignment]
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["email"] == "student@example.com"
    assert payload["items"][0]["role"] == "student"


def test_access_control_routes_role_update_and_revert_success(app, client):
    actor = _fake_user(capabilities={"owner.system.control", "owner.system.read"})
    target_user_id = uuid.uuid4()
    update_audit_id = uuid.uuid4()
    revert_audit_id = uuid.uuid4()

    async def override_current_user():
        return actor

    async def override_db():
        class _DB:
            def __init__(self):
                self.commits = 0

            async def commit(self):
                self.commits += 1

        yield _DB()

    update_item = AccessControlRoleChangeItem(
        audit_id=update_audit_id,
        target_user_id=target_user_id,
        actor_user_id=actor.id,
        action="access_control.role.update",
        previous_role=UserRole.STUDENT,
        next_role=UserRole.MENTOR,
        reason="promote for review support",
        changed_at=datetime.now(timezone.utc),
        reverted_by_audit_id=None,
        is_reversible=True,
    )

    revert_item = AccessControlRoleChangeItem(
        audit_id=update_audit_id,
        target_user_id=target_user_id,
        actor_user_id=actor.id,
        action="access_control.role.update",
        previous_role=UserRole.STUDENT,
        next_role=UserRole.MENTOR,
        reason="promote for review support",
        changed_at=datetime.now(timezone.utc),
        reverted_by_audit_id=revert_audit_id,
        is_reversible=False,
    )

    class FakeAccessControlService:
        def __init__(self, _db):
            pass

        async def update_user_role(self, *, actor_user_id, target_user_id, role, reason):
            assert actor_user_id == actor.id
            assert role == UserRole.MENTOR
            assert reason == "promote for review support"
            assert isinstance(target_user_id, uuid.UUID)
            return update_item

        async def revert_role_change(self, *, actor_user_id, audit_id, reason):
            assert actor_user_id == actor.id
            assert audit_id == update_audit_id
            assert reason == "rollback"
            return revert_item

        async def list_role_changes(self, *, target_user_id=None, limit=50):
            assert target_user_id is None
            assert limit == 50
            return AccessControlRoleChangeListResponse(items=[revert_item], total=1)

    import app.api.v1.routes.access_control as access_control_routes

    original_service = access_control_routes.AccessControlService
    access_control_routes.AccessControlService = FakeAccessControlService  # type: ignore[assignment]
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    update_response = client.patch(
        f"/api/v1/access-control/users/{target_user_id}/role",
        json={"role": "mentor", "reason": "promote for review support"},
        headers={"Authorization": "Bearer fake"},
    )
    revert_response = client.post(
        f"/api/v1/access-control/role-changes/{update_audit_id}/revert",
        json={"reason": "rollback"},
        headers={"Authorization": "Bearer fake"},
    )
    list_changes_response = client.get(
        "/api/v1/access-control/role-changes",
        headers={"Authorization": "Bearer fake"},
    )

    access_control_routes.AccessControlService = original_service  # type: ignore[assignment]
    app.dependency_overrides.clear()

    assert update_response.status_code == 200
    assert update_response.json()["next_role"] == "mentor"
    assert update_response.json()["is_reversible"] is True

    assert revert_response.status_code == 200
    assert revert_response.json()["reverted_by_audit_id"] == str(revert_audit_id)
    assert revert_response.json()["is_reversible"] is False

    assert list_changes_response.status_code == 200
    payload = list_changes_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["audit_id"] == str(update_audit_id)
