"""Trial-plan lifecycle Celery tasks.

The Q2-2026 Air University exhibition launch grants Pro for 30 days from
the moment a student redeems an invite code (``InviteCode.trial_days``).
This module owns the **expire** side of that lifecycle: a daily 02:00 UTC
(07:00 PKT) cron sweeps every user whose ``plan_expires_at`` has fallen
into the past and downgrades them back to ``free``. The cron is
idempotent — re-running the same UTC day is a no-op once the sweep has
processed every expired row.

We deliberately keep this in ``app.tasks`` rather than ``app.services``
because it is a scheduled side-effect (no caller, no HTTP path) and
because the existing ``alert_tasks`` / ``reminder_tasks`` neighbours
follow the same shape: an ``async def`` helper for direct testability
plus a thin ``@celery_app.task`` wrapper that ``asyncio.run``s it.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models import User
from app.tasks.celery_app import celery_app


logger = logging.getLogger(__name__)


async def expire_trial_plans(db: AsyncSession) -> int:
    """Downgrade every user whose ``plan_expires_at`` is in the past.

    Returns the number of rows touched so the Celery task body can log a
    structured summary. ``plan`` is reset to ``"free"`` and
    ``plan_expires_at`` cleared so the next run sees zero candidates.
    Users whose ``plan_expires_at`` is null (= non-trial, never expires)
    or in the future are left alone.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(User)
        .where(User.plan_expires_at.is_not(None))
        .where(User.plan_expires_at < now)
        .where(User.plan != "free")
        .values(plan="free", plan_expires_at=None)
    )
    await db.commit()
    rowcount = int(result.rowcount or 0)
    if rowcount:
        logger.info("trial_tasks.expire_trial_plans expired=%d", rowcount)
    return rowcount


async def _run_expire_trial_plans_async() -> int:
    async with async_session_factory() as db:
        return await expire_trial_plans(db)


@celery_app.task(name="tasks.expire_trial_plans")
def run_expire_trial_plans() -> int:
    """Celery entry point — scheduled daily 02:00 UTC via beat."""
    return asyncio.run(_run_expire_trial_plans_async())
