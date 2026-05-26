import pytest
from unittest.mock import AsyncMock, MagicMock

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
    clerk_api.users.get = AsyncMock(return_value=MagicMock(
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
    clerk_api.users.get = AsyncMock(return_value=MagicMock(
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
