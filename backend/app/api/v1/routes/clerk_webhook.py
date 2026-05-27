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
        await ensure_local_user_async(data["id"], session=db)
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
