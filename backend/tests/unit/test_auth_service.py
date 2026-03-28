import pytest
from types import SimpleNamespace

from app.core.security import create_refresh_token, hash_password
from app.models import UserRole
from app.schemas.auth import UserCreate, UserLogin
from app.services.auth import AuthService
from scholarai_common.errors import ScholarAIException, ErrorCode

pytestmark = pytest.mark.asyncio


class ScalarResult:
    def __init__(self, one=None, all_items=None):
        self.one = one
        self.all_items = all_items or []

    def scalar_one_or_none(self):
        return self.one

    def all(self):
        return self.all_items


class FakeSession:
    def __init__(self, results):
        self.results = list(results)
        self.added = []
        self.execute_count = 0

    async def execute(self, query):
        self.execute_count += 1
        if not self.results:
            raise AssertionError(
                f"FakeSession.execute called {self.execute_count} times but no "
                f"result was configured for query: {query!r}"
            )
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
            password="Strongpass1!",
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
        role=UserRole.STUDENT,
        is_active=True,
        institution_id=None,
        auth_token_version=0,
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
        role=UserRole.STUDENT,
        is_active=True,
        institution_id=None,
        auth_token_version=0,
    )
    session = FakeSession(
        [
            ScalarResult(one=user),
            ScalarResult(all_items=[]),
            ScalarResult(all_items=[]),
        ]
    )
    service = AuthService(session)

    tokens = await service.login(
        UserLogin(email="student@example.com", password="correct-password")
    )

    assert tokens is not None
    assert tokens.access_token
    assert tokens.refresh_token
    assert session.execute_count == 3
    assert not session.results


async def test_auth_service_refresh_session_returns_new_tokens():
    user = SimpleNamespace(
        id="user-1",
        email="student@example.com",
        password_hash=hash_password("correct-password"),
        role=UserRole.STUDENT,
        is_active=True,
        institution_id=None,
        auth_token_version=0,
    )
    session = FakeSession(
        [
            ScalarResult(one=user),
            ScalarResult(all_items=[]),
            ScalarResult(all_items=[]),
            ScalarResult(one=user),
            ScalarResult(all_items=[]),
            ScalarResult(all_items=[]),
        ]
    )
    service = AuthService(session)

    login_tokens = await service.login(
        UserLogin(email="student@example.com", password="correct-password")
    )

    refreshed = await service.refresh_session(login_tokens.refresh_token)

    assert refreshed.access_token
    assert refreshed.refresh_token
    assert refreshed.expires_in > 0
    assert session.execute_count == 6
    assert not session.results


async def test_auth_service_refresh_session_rejects_missing_subject_claim():
    session = FakeSession([])
    service = AuthService(session)
    refresh_token = create_refresh_token({"role": UserRole.STUDENT.value, "token_version": 0})

    with pytest.raises(ScholarAIException) as caught:
        await service.refresh_session(refresh_token)

    assert caught.value.code == ErrorCode.AUTH_TOKEN_EXPIRED
    assert caught.value.status_code == 401
    assert session.execute_count == 0


async def test_auth_service_refresh_session_rejects_unknown_user():
    session = FakeSession([ScalarResult(one=None)])
    service = AuthService(session)
    refresh_token = create_refresh_token(
        {"sub": "missing-user", "role": UserRole.STUDENT.value, "token_version": 0}
    )

    with pytest.raises(ScholarAIException) as caught:
        await service.refresh_session(refresh_token)

    assert caught.value.code == ErrorCode.NOT_FOUND
    assert caught.value.status_code == 401
    assert session.execute_count == 1


async def test_auth_service_refresh_session_rejects_inactive_user():
    user = SimpleNamespace(
        id="user-2",
        email="student@example.com",
        password_hash=hash_password("correct-password"),
        role=UserRole.STUDENT,
        is_active=False,
        institution_id=None,
        auth_token_version=0,
    )
    session = FakeSession([ScalarResult(one=user)])
    service = AuthService(session)
    refresh_token = create_refresh_token(
        {"sub": str(user.id), "role": user.role.value, "token_version": 0}
    )

    with pytest.raises(ScholarAIException) as caught:
        await service.refresh_session(refresh_token)

    assert caught.value.code == ErrorCode.AUTH_INACTIVE_ACCOUNT
    assert caught.value.status_code == 403
    assert session.execute_count == 1


async def test_auth_service_refresh_session_rejects_token_version_mismatch():
    user = SimpleNamespace(
        id="user-3",
        email="student@example.com",
        password_hash=hash_password("correct-password"),
        role=UserRole.STUDENT,
        is_active=True,
        institution_id=None,
        auth_token_version=2,
    )
    session = FakeSession([ScalarResult(one=user)])
    service = AuthService(session)
    refresh_token = create_refresh_token(
        {"sub": str(user.id), "role": user.role.value, "token_version": 1}
    )

    with pytest.raises(ScholarAIException) as caught:
        await service.refresh_session(refresh_token)

    assert caught.value.code == ErrorCode.AUTH_TOKEN_EXPIRED
    assert caught.value.status_code == 401
    assert session.execute_count == 1


async def test_auth_service_logout_increments_token_version():
    user = SimpleNamespace(
        id="user-4",
        email="student@example.com",
        password_hash=hash_password("correct-password"),
        role=UserRole.STUDENT,
        is_active=True,
        institution_id=None,
        auth_token_version=0,
    )
    session = FakeSession([])
    service = AuthService(session)

    await service.logout(user=user)

    assert user.auth_token_version == 1
