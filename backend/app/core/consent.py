"""Consent capture + verification (Feature 9.5, PRD §9.5).

Records every grant / revoke in an immutable audit log alongside the IP,
user-agent, and document hash that the user accepted. Returns HTTP 451
(Unavailable for Legal Reasons) on protected routes when the user has not
accepted the latest version of a required legal document.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import ConsentAuditLog, LegalDocument, User


logger = logging.getLogger(__name__)


ALLOWED_CONSENT_TYPES = {"terms", "privacy", "marketing", "b2b_share", "cookies", "aup"}


@dataclass
class ConsentRecord:
    consent_type: str
    version: str
    granted: bool
    granted_at: datetime | None


def hash_document_body(body: str) -> str:
    return hashlib.sha256((body or "").encode("utf-8")).hexdigest()


async def get_current_legal_doc(db: AsyncSession, slug: str) -> LegalDocument | None:
    result = await db.execute(
        select(LegalDocument)
        .where(LegalDocument.slug == slug, LegalDocument.is_current.is_(True))
        .order_by(LegalDocument.effective_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def record_consent(
    db: AsyncSession,
    user: User,
    *,
    consent_type: str,
    version: str,
    granted: bool,
    request: Request | None = None,
    document_sha256: str | None = None,
) -> ConsentAuditLog:
    if consent_type not in ALLOWED_CONSENT_TYPES:
        raise ValueError(f"Unknown consent type: {consent_type}")

    ip = None
    user_agent = None
    if request is not None:
        ip = (request.client.host if request.client else None) or request.headers.get("x-forwarded-for")
        user_agent = request.headers.get("user-agent")

    entry = ConsentAuditLog(
        user_id=user.id,
        consent_type=consent_type,
        version=version,
        action="grant" if granted else "revoke",
        ip=(ip or "")[:64] or None,
        user_agent=user_agent,
        document_sha256=document_sha256,
    )
    db.add(entry)

    # Mirror onto the denormalised User columns for hot-path checks.
    now = datetime.now(timezone.utc)
    if consent_type == "privacy":
        user.data_consent_version = version
        user.data_consent_granted_at = now if granted else None
        user.data_consent_ip = entry.ip
        user.data_consent_user_agent = user_agent
    elif consent_type == "marketing":
        user.marketing_consent = bool(granted)
    elif consent_type == "b2b_share":
        user.b2b_share_consent = bool(granted)
        user.b2b_share_consent_at = now if granted else None

    await db.flush()
    return entry


async def latest_consent(
    db: AsyncSession,
    user_id: uuid.UUID,
    consent_type: str,
) -> ConsentRecord | None:
    result = await db.execute(
        select(ConsentAuditLog)
        .where(
            ConsentAuditLog.user_id == user_id,
            ConsentAuditLog.consent_type == consent_type,
        )
        .order_by(ConsentAuditLog.granted_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return ConsentRecord(
        consent_type=row.consent_type,
        version=row.version,
        granted=row.action == "grant",
        granted_at=row.granted_at,
    )


def require_consent(consent_type: str):
    """FastAPI dependency. Raises HTTP 451 when the user has not granted the
    current version of the named legal document."""

    if consent_type not in ALLOWED_CONSENT_TYPES:
        raise ValueError(f"Unknown consent type: {consent_type}")

    async def _check(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        record = await latest_consent(db, current_user.id, consent_type)
        if record is None or not record.granted:
            raise HTTPException(
                status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                detail={
                    "error": "consent_required",
                    "consent_type": consent_type,
                    "message": (
                        f"You must accept the current {consent_type} document to continue."
                    ),
                },
            )
        # Version mismatch: a newer document was published after grant.
        current_doc = await get_current_legal_doc(db, consent_type)
        if current_doc is not None and current_doc.version != record.version:
            raise HTTPException(
                status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                detail={
                    "error": "consent_version_outdated",
                    "consent_type": consent_type,
                    "current_version": current_doc.version,
                    "your_version": record.version,
                    "message": (
                        f"The {consent_type} document has been updated. "
                        "Please review and re-accept to continue."
                    ),
                },
            )
        return current_user

    return _check
