from unittest.mock import MagicMock

import pytest

from app.models.models import User
from scripts.clerk_bulk_import import import_user


@pytest.fixture
def user_with_clerk_id(db_session):
    user = User(
        email="linked@x.com",
        password_hash="x",
        full_name="Linked User",
        clerk_user_id="user_already_linked",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def user_no_clerk_id(db_session):
    user = User(
        email="new@x.com",
        password_hash="x",
        full_name="New User",
        clerk_user_id=None,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.mark.asyncio
async def test_import_user_skips_already_linked(db_session, user_with_clerk_id):
    api = MagicMock()
    # clerk-backend-api 1.6.0 SDK is sync — mock with MagicMock, not AsyncMock.
    api.users.create = MagicMock()
    result = await import_user(user_with_clerk_id, api=api, session=db_session)
    assert result == "skipped"
    api.users.create.assert_not_called()


@pytest.mark.asyncio
async def test_import_user_creates_in_clerk_and_links(db_session, user_no_clerk_id):
    api = MagicMock()
    api.users.create = MagicMock(return_value=MagicMock(id="user_clerk_xyz"))
    result = await import_user(user_no_clerk_id, api=api, session=db_session)
    assert result == "imported"
    db_session.refresh(user_no_clerk_id)
    assert user_no_clerk_id.clerk_user_id == "user_clerk_xyz"
