from types import SimpleNamespace
from uuid import uuid4

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole


class _Result:
    def __init__(self, rowcount):
        self.rowcount = rowcount


class _FakeDB:
    def __init__(self):
        self.committed = False
        self.statements = []

    async def execute(self, stmt):
        self.statements.append(stmt)
        return _Result(4)

    async def commit(self):
        self.committed = True

    async def flush(self):
        pass

    async def refresh(self, obj):
        pass


def test_usage_ledger_reset_requires_admin(app, client):
    async def override_current_user():
        return SimpleNamespace(
            id=uuid4(), role=UserRole.STUDENT, is_active=True,
            _token_capabilities=set(),
        )

    async def override_db():
        yield _FakeDB()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    target = uuid4()
    response = client.post(
        f"/api/v1/analytics/usage-ledger/reset?user_id={target}",
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()
    assert response.status_code == 403


def test_usage_ledger_reset_admin_clears_period(app, client):
    fake_db = _FakeDB()

    async def override_current_user():
        return SimpleNamespace(
            id=uuid4(), role=UserRole.ADMIN, is_active=True,
            _token_capabilities=set(),
        )

    async def override_db():
        yield fake_db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    target = uuid4()
    response = client.post(
        f"/api/v1/analytics/usage-ledger/reset?user_id={target}",
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "reset"
    assert body["rows_deleted"] == 4
    assert fake_db.committed is True
