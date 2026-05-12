"""Account-deletion service (Feature 9.5, PRD §9.5).

Schedules a 30-day deletion window. A Celery beat task (wired in a
follow-up PR) processes ``status='pending'`` requests where
``scheduled_for <= now()`` and anonymises every PII column on the user
row while keeping aggregate analytics anchors.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DataDeletionRequest,
    StudentProfile,
    User,
)


logger = logging.getLogger(__name__)

DELETION_WINDOW = timedelta(days=30)
RETAIN_AUDIT_FOR = timedelta(days=365 * 7)  # 7-year consent log retention


class DeletionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def schedule(self, user: User, reason: str | None = None) -> DataDeletionRequest:
        existing = await self._pending_for_user(user.id)
        if existing is not None:
            return existing

        scheduled_for = datetime.now(timezone.utc) + DELETION_WINDOW
        record = DataDeletionRequest(
            user_id=user.id,
            scheduled_for=scheduled_for,
            reason=reason,
            status="pending",
        )
        user.gdpr_erasure_requested_at = datetime.now(timezone.utc)
        self.db.add(record)
        await self.db.flush()
        return record

    async def cancel(self, user_id: uuid.UUID) -> bool:
        record = await self._pending_for_user(user_id)
        if record is None:
            return False
        record.status = "cancelled"
        record.cancelled_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def execute_due(self, *, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        result = await self.db.execute(
            select(DataDeletionRequest).where(
                DataDeletionRequest.status == "pending",
                DataDeletionRequest.scheduled_for <= now,
            )
        )
        executed = 0
        for record in result.scalars().all():
            user = await self.db.get(User, record.user_id)
            if user is not None:
                await self._anonymise_user(user)
            record.status = "executed"
            record.executed_at = now
            executed += 1
        await self.db.flush()
        return executed

    async def _pending_for_user(self, user_id: uuid.UUID) -> DataDeletionRequest | None:
        result = await self.db.execute(
            select(DataDeletionRequest)
            .where(
                DataDeletionRequest.user_id == user_id,
                DataDeletionRequest.status == "pending",
            )
            .order_by(DataDeletionRequest.requested_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _anonymise_user(self, user: User) -> None:
        suffix = uuid.uuid4().hex[:12]
        user.email = f"deleted-{suffix}@scholarai.invalid"
        user.password_hash = "DELETED"
        user.full_name = "[deleted]"
        user.account_deleted_at = datetime.now(timezone.utc)
        user.is_active = False
        user.marketing_consent = False
        user.b2b_share_consent = False
        user.data_consent_ip = None
        user.data_consent_user_agent = None
        user.parent_consent_email = None
        user.date_of_birth = None

        profile_result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile is None:
            return
        for field in (
            "phone_e164",
            "whatsapp_e164",
            "father_occupation",
            "current_employer",
            "current_job_title",
            "linkedin_url",
            "github_url",
            "pakistani_university",
            "city_of_origin",
            "degree_subject",
            "notes" if hasattr(profile, "notes") else None,
        ):
            if field is not None and hasattr(profile, field):
                setattr(profile, field, None)
        profile.lead_score = 0
        profile.household_income_band = None
