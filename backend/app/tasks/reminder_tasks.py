"""Deadline reminder Celery task (PRD §0.6 / §0.5 freemium model).

Daily sweep over tracker items with an upcoming deadline. Plan-aware fan-out
with the PRD's "30-day silent stop" for free accounts:

    free        -> email only, and ONLY within the first 30 days of the account.
                   After 30 days reminders silently stop (the silence is the hook).
    pro         -> email only, always on.
    elite       -> email + WhatsApp, always on (Q1 retier — SMS removed).
    institution -> email + WhatsApp, always on.

Channels are log-only stubs (see app/services/notifications). The async core
is unit-tested directly; the Celery wrapper bridges sync -> async.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.models import ApplicationTrackerItem, User, UserPlan
from app.services.notifications import PLAN_CHANNELS, fan_out_for_plan
from app.tasks.celery_app import celery_app


logger = logging.getLogger(__name__)

REMINDER_WINDOW_DAYS = 14
FREE_REMINDER_GRACE_DAYS = 30


async def _run_deadline_reminders_async() -> dict[str, int]:
    now = datetime.now(timezone.utc)
    today = now.date()
    window_end = today + timedelta(days=REMINDER_WINDOW_DAYS)
    free_cutoff = now - timedelta(days=FREE_REMINDER_GRACE_DAYS)

    async with async_session_factory() as session:
        # One join: pull every tracker item with an upcoming deadline together
        # with its owning User (+ student_profile for phone numbers). The
        # free-account 30-day cutoff is applied in SQL, so users past the
        # grace window never load.
        rows = list(
            (
                await session.execute(
                    select(ApplicationTrackerItem, User)
                    .join(User, User.id == ApplicationTrackerItem.user_id)
                    .options(selectinload(User.student_profile))
                    .where(
                        ApplicationTrackerItem.deadline.is_not(None),
                        ApplicationTrackerItem.deadline >= today,
                        ApplicationTrackerItem.deadline <= window_end,
                        User.is_active.is_(True),
                        or_(
                            User.plan != UserPlan.FREE.value,
                            User.created_at >= free_cutoff,
                        ),
                    )
                )
            ).all()
        )
        if not rows:
            return {
                "items_due": 0,
                "users_notified": 0,
                "reminders_sent": 0,
                "skipped_free_expired": 0,
            }

        by_user: dict[str, tuple[User, list[ApplicationTrackerItem]]] = {}
        for item, user in rows:
            uid = str(user.id)
            if uid in by_user:
                by_user[uid][1].append(item)
            else:
                by_user[uid] = (user, [item])

        users_notified = 0
        reminders_sent = 0
        for user, user_items in by_user.values():
            lines: list[str] = []
            for item in sorted(user_items, key=lambda i: i.deadline or window_end):
                name = item.program_name or item.university_name or "Tracked application"
                days_left = (item.deadline - today).days if item.deadline else None
                lines.append(f"{name} — deadline in {days_left} day(s)")
            subject = "Your application deadlines are approaching"
            body = "Upcoming application deadlines on your tracker:\n" + "\n".join(lines)
            message = f"{subject}\n\n{body}"
            await fan_out_for_plan(session, user, message)
            plan_key = (user.plan or "free").lower()
            channels = PLAN_CHANNELS.get(plan_key, ("email",))
            if channels:
                users_notified += 1
                reminders_sent += len(channels)

        logger.info(
            "deadline_reminders items=%d users_notified=%d reminders_sent=%d",
            len(rows),
            users_notified,
            reminders_sent,
        )
        return {
            "items_due": len(rows),
            "users_notified": users_notified,
            "reminders_sent": reminders_sent,
            "skipped_free_expired": 0,  # filtered in SQL — kept for response shape stability
        }


@celery_app.task(name="tasks.run_deadline_reminders")
def run_deadline_reminders() -> dict[str, int]:
    return asyncio.run(_run_deadline_reminders_async())
