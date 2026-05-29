"""Migrate existing app users into Clerk. Idempotent on User.clerk_user_id."""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.integrations.clerk.client import clerk_client
from app.models.models import User

log = logging.getLogger(__name__)


async def import_user(user: User, *, api, session) -> str:
    """Create a Clerk user for the given local row and link via clerk_user_id.

    Idempotent: returns "skipped" if the row already carries a clerk_user_id.
    Returns "imported" on first-time link.
    """
    if user.clerk_user_id:
        return "skipped"
    # clerk-backend-api 1.6.0 SDK is sync — do NOT await (same class as the
    # df37604 fix on api.users.get).
    created = api.users.create({
        "email_address": [user.email],
        "first_name": user.full_name.split(" ", 1)[0] if user.full_name else None,
        "last_name": user.full_name.split(" ", 1)[1] if user.full_name and " " in user.full_name else None,
        "skip_password_requirement": True,
    })
    user.clerk_user_id = created.id
    if isinstance(session, AsyncSession):
        await session.commit()
    else:
        session.commit()
    return "imported"


async def main() -> None:
    api = clerk_client()
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.clerk_user_id.is_(None))
        )
        users = result.scalars().all()
        for user in users:
            try:
                outcome = await import_user(user, api=api, session=session)
                log.info("user=%s outcome=%s", user.id, outcome)
            except Exception as exc:
                log.exception("import failed for user=%s: %s", user.id, exc)


if __name__ == "__main__":
    asyncio.run(main())
