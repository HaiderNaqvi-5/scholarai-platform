"""Application tracker service (Feature 6, PRD §6).

Free-tier cap: 3 items. Beyond that the create endpoint returns HTTP 402
with the count of upcoming deadlines the student is *not* tracking, so the
frontend's <UpgradeWall /> can render a specific, calibrated prompt.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_guard import (
    get_price_for_currency,
    has_plan_at_least,
    raise_plan_required,
)
from app.models import (
    ApplicationTrackerItem,
    RecordState,
    Scholarship,
    TRACKER_STAGES,
    User,
    default_document_checklist,
)
from app.schemas.tracker import (
    TrackerChecklistPatchRequest,
    TrackerItemCreateRequest,
    TrackerStageUpdateRequest,
)


FREE_PLAN_ITEM_LIMIT = 3


class TrackerService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_items(self, user_id: uuid.UUID) -> list[ApplicationTrackerItem]:
        result = await self.db.execute(
            select(ApplicationTrackerItem)
            .where(ApplicationTrackerItem.user_id == user_id)
            .order_by(ApplicationTrackerItem.deadline.asc().nullslast(),
                      ApplicationTrackerItem.created_at.asc())
        )
        return list(result.scalars().all())

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(ApplicationTrackerItem)
            .where(ApplicationTrackerItem.user_id == user_id)
        )
        return int(result.scalar() or 0)

    async def create(
        self,
        user: User,
        payload: TrackerItemCreateRequest,
    ) -> ApplicationTrackerItem:
        if not has_plan_at_least(user, "pro", "elite", "institution"):
            current = await self.count_for_user(user.id)
            if current >= FREE_PLAN_ITEM_LIMIT:
                untracked = await self._count_untracked_upcoming_deadlines(user.id)
                price = get_price_for_currency(user.plan_currency)
                raise_plan_required(
                    user,
                    ["pro", "elite", "institution"],
                    message=(
                        f"You have {untracked} upcoming scholarship deadlines you are "
                        f"not tracking. Unlimited tracking with Pro ({price})."
                    ),
                    extra={
                        "error": "plan_limit_reached",
                        "current_items": current,
                        "free_limit": FREE_PLAN_ITEM_LIMIT,
                        "untracked_count": untracked,
                    },
                )

        item = ApplicationTrackerItem(
            user_id=user.id,
            scholarship_id=payload.scholarship_id,
            university_id=payload.university_id,
            program_name=payload.program_name,
            university_name=payload.university_name,
            country=payload.country,
            stage=payload.stage,
            deadline=payload.deadline,
            notes=payload.notes,
            document_checklist=default_document_checklist(),
        )

        # Optionally hydrate program/university/country/deadline from a linked scholarship
        if payload.scholarship_id and not (payload.program_name and payload.country):
            scholarship = await self.db.get(Scholarship, payload.scholarship_id)
            if scholarship is not None:
                if not item.program_name:
                    item.program_name = scholarship.title
                if not item.university_name:
                    item.university_name = scholarship.provider_name
                if not item.country and scholarship.country_code:
                    item.country = scholarship.country_code
                if not item.deadline and scholarship.deadline_at:
                    item.deadline = scholarship.deadline_at.date()

        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update_stage(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        payload: TrackerStageUpdateRequest,
    ) -> ApplicationTrackerItem | None:
        item = await self._get_owned(user_id, item_id)
        if item is None:
            return None
        item.stage = payload.stage
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update_checklist(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        payload: TrackerChecklistPatchRequest,
    ) -> ApplicationTrackerItem | None:
        item = await self._get_owned(user_id, item_id)
        if item is None:
            return None
        merged = dict(item.document_checklist or {})
        for key, value in payload.checklist.items():
            merged[key] = bool(value)
        item.document_checklist = merged
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, user_id: uuid.UUID, item_id: uuid.UUID) -> bool:
        item = await self._get_owned(user_id, item_id)
        if item is None:
            return False
        await self.db.delete(item)
        await self.db.flush()
        return True

    async def _get_owned(
        self, user_id: uuid.UUID, item_id: uuid.UUID
    ) -> ApplicationTrackerItem | None:
        result = await self.db.execute(
            select(ApplicationTrackerItem).where(
                ApplicationTrackerItem.id == item_id,
                ApplicationTrackerItem.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _count_untracked_upcoming_deadlines(self, user_id: uuid.UUID) -> int:
        soon = datetime.now(timezone.utc) + timedelta(days=60)
        tracked_subq = (
            select(ApplicationTrackerItem.scholarship_id)
            .where(
                ApplicationTrackerItem.user_id == user_id,
                ApplicationTrackerItem.scholarship_id.is_not(None),
            )
        ).subquery()
        result = await self.db.execute(
            select(func.count())
            .select_from(Scholarship)
            .where(
                Scholarship.record_state == RecordState.PUBLISHED,
                Scholarship.deadline_at.is_not(None),
                Scholarship.deadline_at <= soon,
                ~Scholarship.id.in_(select(tracked_subq.c.scholarship_id)),
            )
        )
        return int(result.scalar() or 0)
