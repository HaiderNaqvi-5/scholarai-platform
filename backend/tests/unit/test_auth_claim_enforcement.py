from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core import dependencies
from app.core.config import settings
from app.models import UserRole
from scholarai_common.errors import ScholarAIException


@pytest.fixture(autouse=True)
def _force_local_auth(monkeypatch):
    # These tests exercise the local-JWT scope-claim path (decode_token is
    # monkeypatched below). Pin AUTH_PROVIDER=local so an ambient .env with
    # AUTH_PROVIDER=clerk does not route get_current_user to the Clerk path.
    monkeypatch.setattr(settings, "AUTH_PROVIDER", "local")


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


def _user(role: UserRole, institution_id=None, auth_token_version=0):
    return SimpleNamespace(
        id=uuid4(),
        email="tester@example.com",
        role=role,
        institution_id=institution_id,
        is_active=True,
        auth_token_version=auth_token_version,
    )


async def test_get_current_user_rejects_non_list_capabilities(monkeypatch):
    user = _user(UserRole.ADMIN)
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token, expected_type="access": {
            "sub": str(user.id),
            "capabilities": "admin.audit.read",
            "token_version": user.auth_token_version,
        },
    )

    with pytest.raises(ScholarAIException) as caught:
        await dependencies.get_current_user(token="fake", db=_FakeDB(user))

    assert caught.value.status_code == 401
    assert caught.value.code.value == "auth_token_expired"


async def test_get_current_user_rejects_non_string_capabilities(monkeypatch):
    user = _user(UserRole.ADMIN)
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token, expected_type="access": {
            "sub": str(user.id),
            "capabilities": ["admin.audit.read", 7],
            "token_version": user.auth_token_version,
        },
    )

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
            "token_version": user.auth_token_version,
        },
    )

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
            "token_version": user.auth_token_version,
        },
    )

    with pytest.raises(ScholarAIException) as caught:
        await dependencies.get_current_user(token="fake", db=_FakeDB(user))

    assert caught.value.status_code == 403
    assert caught.value.code.value == "auth_scope_forbidden"


# ── P2-1: dead Redis session cache removed ────────────────────────────────────

class _RecordingFakeDB(_FakeDB):
    """FakeDB that also records which queries were executed (for no-Redis assertion)."""
    def __init__(self, user):
        super().__init__(user)
        self.executed = []

    async def execute(self, query):
        self.executed.append(query)
        return _FakeResult(self._user)


async def test_auth_dependency_makes_no_redis_calls(monkeypatch):
    """After P2-1 removal the auth path must not call redis_client.get or .setex.

    We install a sentinel redis_client on the module; if the dependency reaches
    it, the test fails. Because redis_client is no longer imported by the module,
    this test also verifies the import was cleaned up: patching a non-existent
    attribute via monkeypatch will raise AttributeError — so we use setattr to
    inject, then assert it was never touched.
    """
    user = _user(UserRole.STUDENT)
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token, expected_type="access": {
            "sub": str(user.id),
            "capabilities": [],
            "token_version": user.auth_token_version,
        },
    )

    calls: list[str] = []

    class _SentinelRedis:
        async def get(self, key):
            calls.append(f"get:{key}")
            return None

        async def setex(self, key, ttl, payload):
            calls.append(f"setex:{key}")

    # Inject onto the module object (not via monkeypatch.setattr so we don't
    # require the attribute to pre-exist on the module).
    original = getattr(dependencies, "redis_client", None)
    dependencies.redis_client = _SentinelRedis()  # type: ignore[attr-defined]
    try:
        result = await dependencies.get_current_user(token="fake", db=_RecordingFakeDB(user))
    finally:
        if original is None:
            del dependencies.redis_client
        else:
            dependencies.redis_client = original

    assert calls == [], (
        f"Auth dependency called Redis after P2-1 removal: {calls}"
    )
    assert result is user


async def test_auth_dependency_revokes_stale_token_version(monkeypatch):
    """A token whose token_version != user.auth_token_version must be rejected 401.

    This is the real revocation guard that the removed Redis cache could have
    bypassed had its read path ever been completed.
    """
    user = _user(UserRole.STUDENT, auth_token_version=2)  # DB version = 2
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token, expected_type="access": {
            "sub": str(user.id),
            "capabilities": [],
            "token_version": 1,  # stale — issued before last revocation
        },
    )

    with pytest.raises(ScholarAIException) as caught:
        await dependencies.get_current_user(token="fake", db=_FakeDB(user))

    assert caught.value.status_code == 401
    assert caught.value.code.value == "auth_token_expired"
