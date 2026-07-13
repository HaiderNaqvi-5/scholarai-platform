import pytest
from unittest.mock import MagicMock

from app.integrations.clerk.user_sync import ensure_local_user
from app.models.models import User


@pytest.mark.asyncio
async def test_existing_user_returned(db_session):
    existing = User(
        email="x@x.com", password_hash="x", full_name="Existing",
        clerk_user_id="user_existing",
    )
    db_session.add(existing)
    db_session.commit()
    result = await ensure_local_user(
        "user_existing", clerk_api=MagicMock(), session=db_session,
    )
    assert result.id == existing.id


@pytest.mark.asyncio
async def test_missing_user_created_from_clerk(db_session):
    clerk_api = MagicMock()
    # clerk-backend-api 1.6.0 SDK is sync — mock with MagicMock (not AsyncMock)
    # so users.get() returns the object directly, matching production.
    clerk_api.users.get = MagicMock(return_value=MagicMock(
        id="user_new",
        email_addresses=[MagicMock(email_address="new@x.com", id="e1")],
        primary_email_address_id="e1",
        first_name="New",
        last_name="User",
    ))
    result = await ensure_local_user(
        "user_new", clerk_api=clerk_api, session=db_session,
    )
    assert result.clerk_user_id == "user_new"
    assert result.email == "new@x.com"
    assert result.full_name == "New User"


@pytest.mark.asyncio
async def test_email_collision_links_existing(db_session):
    db_session.add(User(
        email="dup@x.com", password_hash="x", full_name="Dup",
        clerk_user_id=None,
    ))
    db_session.commit()
    clerk_api = MagicMock()
    clerk_api.users.get = MagicMock(return_value=MagicMock(
        id="user_clerk_dup",
        email_addresses=[MagicMock(email_address="dup@x.com", id="e1")],
        primary_email_address_id="e1",
        first_name=None, last_name=None,
    ))
    result = await ensure_local_user(
        "user_clerk_dup", clerk_api=clerk_api, session=db_session,
    )
    assert result.clerk_user_id == "user_clerk_dup"
    assert result.email == "dup@x.com"


# ─── Task 34 regression pin: Clerk users must get a non-null sentinel hash ────
#
# users.password_hash is NOT NULL with no server default. Clerk-mode users
# never set a local password, so ensure_local_user[_async] must supply a
# sentinel value at construction time or user creation would hit a NOT NULL
# IntegrityError. Verified already correct (both the sync and async
# variants set `password_hash=f"clerk:{secrets.token_urlsafe(16)}"`) — this
# test pins that behavior against regression rather than introducing a fix.


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def scalar_one_or_none(self):
        return self._row


class _FakeAsyncSession:
    """Minimal duck-typed async session (mirrors test_clerk_webhook.py's
    _FakeAsyncSession) so this test exercises the real ensure_local_user_async
    code path without needing a Postgres TEST_DATABASE_URL."""

    def __init__(self):
        self._store = []

    def add(self, obj):
        self._store.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    async def execute(self, stmt):
        try:
            rendered = str(stmt.compile(compile_kwargs={"literal_binds": True})).lower()
        except Exception:
            rendered = str(stmt).lower()
        for obj in self._store:
            cuid = (obj.clerk_user_id or "").lower()
            if cuid and cuid in rendered:
                return _FakeResult(obj)
            email = (obj.email or "").lower()
            if email and email in rendered:
                return _FakeResult(obj)
        return _FakeResult(None)


@pytest.mark.asyncio
async def test_async_missing_user_created_from_clerk_gets_sentinel_password_hash():
    from app.integrations.clerk.user_sync import ensure_local_user_async
    from app.core.security import verify_password

    clerk_api = MagicMock()
    # clerk-backend-api 1.6.0 SDK is sync — mock with MagicMock (not AsyncMock)
    # so users.get() returns the object directly, matching production.
    clerk_api.users.get = MagicMock(return_value=MagicMock(
        id="user_async_new",
        email_addresses=[MagicMock(email_address="async-new@x.com", id="e1")],
        primary_email_address_id="e1",
        first_name="Async",
        last_name="New",
    ))

    result = await ensure_local_user_async(
        "user_async_new", clerk_api=clerk_api, session=_FakeAsyncSession(),
    )

    assert result.clerk_user_id == "user_async_new"
    assert result.email == "async-new@x.com"
    assert result.password_hash  # non-null / non-empty sentinel

    # The sentinel must never validate as a real password via the local
    # verify path. verify_password raises on a non-pbkdf2 string rather than
    # returning False (UnknownHashError) — either outcome means "no match".
    try:
        matched = verify_password("some-guessed-password", result.password_hash)
    except Exception:
        matched = False
    assert matched is False
