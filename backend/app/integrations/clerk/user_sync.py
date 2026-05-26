from __future__ import annotations

import secrets
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User
from app.integrations.clerk.client import clerk_client


async def ensure_local_user(
    clerk_user_id: str,
    *,
    session: Session,
    clerk_api=None,
) -> User:
    existing = session.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    api = clerk_api if clerk_api is not None else clerk_client()
    clerk_user = await api.users.get(user_id=clerk_user_id)
    primary_email = next(
        (e.email_address for e in clerk_user.email_addresses
         if e.id == clerk_user.primary_email_address_id),
        None,
    )
    if not primary_email:
        raise ValueError(f"Clerk user {clerk_user_id} has no primary email")

    linked = session.execute(
        select(User).where(User.email == primary_email)
    ).scalar_one_or_none()
    if linked is not None:
        linked.clerk_user_id = clerk_user_id
        session.commit()
        return linked

    first = (clerk_user.first_name or "").strip()
    last = (clerk_user.last_name or "").strip()
    full_name = f"{first} {last}".strip() or primary_email

    new = User(
        email=primary_email,
        password_hash=f"clerk:{secrets.token_urlsafe(16)}",
        clerk_user_id=clerk_user_id,
        full_name=full_name,
    )
    session.add(new)
    session.commit()
    session.refresh(new)
    return new


async def ensure_local_user_async(
    clerk_user_id: str,
    *,
    session: AsyncSession,
    clerk_api=None,
) -> User:
    """Async sibling of ensure_local_user for use with AsyncSession.

    Used by _get_user_from_clerk_jwt in app.core.dependencies.
    The sync ensure_local_user is kept unchanged for Task 4 webhook tests.
    """
    result = await session.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    api = clerk_api if clerk_api is not None else clerk_client()
    clerk_user = await api.users.get(user_id=clerk_user_id)
    primary_email = next(
        (e.email_address for e in clerk_user.email_addresses
         if e.id == clerk_user.primary_email_address_id),
        None,
    )
    if not primary_email:
        raise ValueError(f"Clerk user {clerk_user_id} has no primary email")

    result = await session.execute(
        select(User).where(User.email == primary_email)
    )
    linked = result.scalar_one_or_none()
    if linked is not None:
        linked.clerk_user_id = clerk_user_id
        await session.commit()
        return linked

    first = (clerk_user.first_name or "").strip()
    last = (clerk_user.last_name or "").strip()
    full_name = f"{first} {last}".strip() or primary_email

    new = User(
        email=primary_email,
        password_hash=f"clerk:{secrets.token_urlsafe(16)}",
        clerk_user_id=clerk_user_id,
        full_name=full_name,
    )
    session.add(new)
    await session.commit()
    await session.refresh(new)
    return new
