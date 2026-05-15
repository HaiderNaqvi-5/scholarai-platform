"""Application tracker service (Feature 6, PRD §6).

Per-plan tracker caps (Q1 retier): free=3 / pro=6 / elite=12 / institution=50.
The constants live in ``app.core.plan_guard.TRACKER_CAP``; this service reads
them at runtime so the cap is configured in one place.

Hitting the cap returns HTTP 402 with the count of upcoming deadlines the
student is *not* tracking, so the frontend's ``<UpgradeWall />`` can render a
specific, calibrated prompt.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_guard import (
    TRACKER_CAP,
    get_price_for_currency,
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


# Back-compat re-export: prior callers + tests imported ``FREE_PLAN_ITEM_LIMIT``
# from this module. Source of truth is ``plan_guard.TRACKER_CAP["free"]``.
FREE_PLAN_ITEM_LIMIT = TRACKER_CAP["free"]

# Upgrade target ladder by current plan. Institution is at the top of the
# ladder; its cap still fires, but there is no higher tier to upsell to, so we
# point the user at the same plan list (frontend renders "contact sales").
_UPGRADE_TARGETS: dict[str, list[str]] = {
    "free": ["pro", "elite", "institution"],
    "pro": ["elite", "institution"],
    "elite": ["institution"],
    "institution": ["institution"],
}


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
        plan = (user.plan or "free").lower()
        cap = TRACKER_CAP.get(plan, TRACKER_CAP["free"])
        current = await self.count_for_user(user.id)
        if current >= cap:
            untracked = await self._count_untracked_upcoming_deadlines(user.id)
            price = get_price_for_currency(user.plan_currency)
            upgrade_targets = _UPGRADE_TARGETS.get(plan, _UPGRADE_TARGETS["free"])
            if plan == "free":
                message = (
                    f"You have {untracked} upcoming scholarship deadlines you are "
                    f"not tracking. Track up to {TRACKER_CAP['pro']} with Pro "
                    f"({price})."
                )
            else:
                message = (
                    f"Tracker limit reached ({cap} items on {plan}). "
                    f"Upgrade for more capacity ({price})."
                )
            raise_plan_required(
                user,
                upgrade_targets,
                message=message,
                extra={
                    "error": "plan_limit_reached",
                    "current_items": current,
                    "cap": cap,
                    # Kept for backwards-compat with earlier UpgradeWall payloads
                    # that read ``free_limit``; mirrors ``cap`` post-retier.
                    "free_limit": cap,
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
