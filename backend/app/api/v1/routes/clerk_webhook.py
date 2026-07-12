"""
Clerk webhook handler — user lifecycle events.

Handles: user.created, user.updated, user.deleted.
Svix signature verification is performed on every request; unverified
requests are rejected with 401.

Registration: app/api/v1/__init__.py includes this router at prefix /webhooks.
Endpoint: POST /api/v1/webhooks/clerk
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.config import settings
from app.core.database import get_db
from app.integrations.clerk.user_sync import ensure_local_user_async
from app.models.models import User


router = APIRouter(tags=["Webhooks"])


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: str = Header(..., alias="svix-id"),
    svix_timestamp: str = Header(..., alias="svix-timestamp"),
    svix_signature: str = Header(..., alias="svix-signature"),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    if not settings.CLERK_WEBHOOK_SECRET:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "webhook secret not configured")
    try:
        wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
        event = wh.verify(body, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        })
    except WebhookVerificationError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid signature") from exc

    event_type = event.get("type")
    data = event.get("data", {})

    if event_type == "user.created":
        primary_id = data.get("primary_email_address_id")
        primary_email = next(
            (e["email_address"] for e in data.get("email_addresses", [])
             if e.get("id") == primary_id),
            None,
        )
        pre_existing = await _user_exists(
            db, clerk_id=data["id"], email=primary_email
        )
        user = await ensure_local_user_async(data["id"], session=db)
        if not pre_existing and primary_email:
            from app.services.notifications.channels import (
                send_templated_email_best_effort,
            )
            login_url = (
                settings.FRONTEND_BASE_URL.rstrip("/") + "/login"
                if settings.FRONTEND_BASE_URL else ""
            )
            send_templated_email_best_effort(
                to=user.email,
                template="welcome",
                context={"name": user.full_name, "login_url": login_url},
                source="welcome",
            )
    elif event_type == "user.updated":
        await _sync_user_attrs(data, db)
    elif event_type == "user.deleted":
        result = await db.execute(
            select(User).where(User.clerk_user_id == data["id"])
        )
        user = result.scalar_one_or_none()
        if user:
            user.is_active = False
            await db.commit()

    return {"status": "ok"}


async def _user_exists(
    db: AsyncSession, *, clerk_id: str, email: str | None
) -> bool:
    """True iff a User row already exists by clerk_user_id or by email."""
    by_clerk = await db.execute(
        select(User).where(User.clerk_user_id == clerk_id)
    )
    if by_clerk.scalar_one_or_none() is not None:
        return True
    if not email:
        return False
    by_email = await db.execute(select(User).where(User.email == email))
    return by_email.scalar_one_or_none() is not None


async def _sync_user_attrs(data: dict, db: AsyncSession) -> None:
    result = await db.execute(
        select(User).where(User.clerk_user_id == data["id"])
    )
    user = result.scalar_one_or_none()
    if user is None:
        return

    primary_id = data.get("primary_email_address_id")
    new_email = next(
        (e["email_address"] for e in data.get("email_addresses", [])
         if e.get("id") == primary_id),
        None,
    )
    if new_email and new_email != user.email:
        user.email = new_email

    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()
    new_full = f"{first} {last}".strip()
    if new_full and new_full != user.full_name:
        user.full_name = new_full

    await db.commit()
