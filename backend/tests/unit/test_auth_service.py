import pytest
from types import SimpleNamespace

from app.core.security import hash_password
from app.schemas.auth import UserCreate, UserLogin
from app.services.auth import AuthService
from scholarai_common.errors import ScholarAIException, ErrorCode

pytestmark = pytest.mark.asyncio


class ScalarResult:
    def __init__(self, one=None):
        self.one = one

    def scalar_one_or_none(self):
        return self.one


class FakeSession:
    def __init__(self, results):
        self.results = list(results)
        self.added = []

    async def execute(self, _query):
        return self.results.pop(0)

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None

    async def refresh(self, _value):
        return None


async def test_auth_service_register_creates_user():
    session = FakeSession([ScalarResult(one=None)])
    service = AuthService(session)

    user = await service.register(
        UserCreate(
            email="Student@example.com",
            password="strongpass1",
            full_name="Student Name",
        )
    )

    assert user is not None
    assert user.email == "student@example.com"
    assert len(session.added) == 1


async def test_auth_service_login_rejects_invalid_password():
    user = SimpleNamespace(
        id="user-1",
        email="student@example.com",
        password_hash=hash_password("correct-password"),
        role=SimpleNamespace(value="student"),
        is_active=True,
    )
    session = FakeSession([ScalarResult(one=user)])
    service = AuthService(session)

    with pytest.raises(ScholarAIException) as caught:
        await service.login(
            UserLogin(email="student@example.com", password="wrong-password")
        )

    assert caught.value.code == ErrorCode.AUTH_INVALID_CREDENTIALS
    assert caught.value.status_code == 401


async def test_auth_service_login_returns_tokens_for_valid_credentials():
    user = SimpleNamespace(
        id="user-1",
        email="student@example.com",
        password_hash=hash_password("correct-password"),
        role=SimpleNamespace(value="student"),
        is_active=True,
    )
    session = FakeSession([ScalarResult(one=user)])
    service = AuthService(session)

    tokens = await service.login(
        UserLogin(email="student@example.com", password="correct-password")
    )

    assert tokens is not None
    assert tokens.access_token
    assert tokens.refresh_token


async def test_auth_service_refresh_session_returns_new_tokens():
    user = SimpleNamespace(
        id="user-1",
        email="student@example.com",
        password_hash=hash_password("correct-password"),
        role=SimpleNamespace(value="student"),
        is_active=True,
    )
    session = FakeSession([ScalarResult(one=user), ScalarResult(one=user)])
    service = AuthService(session)

    login_tokens = await service.login(
        UserLogin(email="student@example.com", password="correct-password")
    )
    assert login_tokens is not None

    refreshed = await service.refresh_session(login_tokens.refresh_token)

    assert refreshed.access_token
    assert refreshed.refresh_token
    assert refreshed.expires_in > 0
