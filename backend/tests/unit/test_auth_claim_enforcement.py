from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core import dependencies
from app.models import UserRole
from scholarai_common.errors import ScholarAIException

pytestmark = pytest.mark.asyncio


class _FakeResult:
    def __init__(self, user):
        self._user = user

    def scalar_one_or_none(self):
        return self._user


class _FakeDB:
    def __init__(self, user):
        self._user = user

    async def execute(self, _query):
        return _FakeResult(self._user)


class _FakeRedis:
    async def get(self, _key):
        return None

    async def setex(self, _key, _ttl, _payload):
        return None


def _user(role: UserRole, institution_id=None):
    return SimpleNamespace(
        id=uuid4(),
        email="tester@example.com",
        role=role,
        institution_id=institution_id,
        is_active=True,
    )


async def test_get_current_user_rejects_non_list_capabilities(monkeypatch):
    user = _user(UserRole.ADMIN)
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token, expected_type="access": {"sub": str(user.id), "capabilities": "admin.audit.read"},
    )
    monkeypatch.setattr(dependencies, "redis_client", _FakeRedis())

    with pytest.raises(ScholarAIException) as caught:
        await dependencies.get_current_user(token="fake", db=_FakeDB(user))

    assert caught.value.status_code == 401
    assert caught.value.code.value == "auth_token_expired"


async def test_get_current_user_rejects_non_string_capabilities(monkeypatch):
    user = _user(UserRole.ADMIN)
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token, expected_type="access": {"sub": str(user.id), "capabilities": ["admin.audit.read", 7]},
    )
    monkeypatch.setattr(dependencies, "redis_client", _FakeRedis())

    with pytest.raises(ScholarAIException) as caught:
        await dependencies.get_current_user(token="fake", db=_FakeDB(user))

    assert caught.value.status_code == 401
    assert caught.value.code.value == "auth_token_expired"


async def test_get_current_user_rejects_university_missing_scope_claim(monkeypatch):
    institution_id = uuid4()
    user = _user(UserRole.UNIVERSITY, institution_id=institution_id)
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token, expected_type="access": {
            "sub": str(user.id),
            "capabilities": ["university.students.read"],
        },
    )
    monkeypatch.setattr(dependencies, "redis_client", _FakeRedis())

    with pytest.raises(ScholarAIException) as caught:
        await dependencies.get_current_user(token="fake", db=_FakeDB(user))

    assert caught.value.status_code == 403
    assert caught.value.code.value == "auth_scope_forbidden"


async def test_get_current_user_rejects_mismatched_scope_claim(monkeypatch):
    institution_id = uuid4()
    user = _user(UserRole.UNIVERSITY, institution_id=institution_id)
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token, expected_type="access": {
            "sub": str(user.id),
            "capabilities": ["university.students.read"],
            "institution_scope": str(uuid4()),
        },
    )
    monkeypatch.setattr(dependencies, "redis_client", _FakeRedis())

    with pytest.raises(ScholarAIException) as caught:
        await dependencies.get_current_user(token="fake", db=_FakeDB(user))

    assert caught.value.status_code == 403
    assert caught.value.code.value == "auth_scope_forbidden"
