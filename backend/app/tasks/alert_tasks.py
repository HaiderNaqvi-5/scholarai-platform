"""Priority scholarship alerts Celery task (PRD §0.6, Elite feature).

Daily sweep: find published scholarships whose deadline is within 7 days, then
notify users who target that country but have NOT added the scholarship to
their tracker. Plan-aware fan-out (Q1 retier — WhatsApp-only premium):

    free        -> skipped (priority alerts are a paid feature)
    pro         -> email only
    elite       -> email + WhatsApp
    institution -> email + WhatsApp

Channels are log-only stubs (see app/services/notifications) — no Twilio /
WhatsApp integration during FYP. The async core is unit-tested directly; the
Celery wrapper just bridges sync -> async.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.models import (
    ApplicationTrackerItem,
    RecordState,
    Scholarship,
    User,
    UserPlan,
)
from app.services.notifications import PLAN_CHANNELS, fan_out_for_plan
from app.tasks.celery_app import celery_app
from app.utils.profile_targets import resolve_target_countries


logger = logging.getLogger(__name__)

ALERT_WINDOW_DAYS = 7

# Plan strings that opt into priority alerts. Free is excluded — alerts are a
# paid feature. Mirror of UserPlan members above FREE.
_PAID_PLANS = {UserPlan.PRO.value, UserPlan.ELITE.value, UserPlan.INSTITUTION.value}


async def _run_priority_scholarship_alerts_async() -> dict[str, int]:
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=ALERT_WINDOW_DAYS)

    async with async_session_factory() as session:
        scholarships = list(
            (
                await session.execute(
                    select(Scholarship).where(
                        Scholarship.record_state == RecordState.PUBLISHED,
                        Scholarship.deadline_at.is_not(None),
                        Scholarship.deadline_at > now,
                        Scholarship.deadline_at <= cutoff,
                    )
                )
            )
            .scalars()
            .all()
        )
        if not scholarships:
            return {"scholarships_due": 0, "users_notified": 0, "alerts_sent": 0}

        # Bucket scholarships by their (upper-cased) country code so per-user
        # filtering is O(targets), not O(scholarships).
        scholarships_by_country: dict[str, list[Scholarship]] = defaultdict(list)
        for s in scholarships:
            scholarships_by_country[(s.country_code or "").upper()].append(s)

        # Filter free + inactive in SQL so the result set is bounded to the
        # set we actually fan-out to.
        users = list(
            (
                await session.execute(
                    select(User)
                    .options(selectinload(User.student_profile))
                    .where(
                        User.is_active.is_(True),
                        User.plan.in_(list(_PAID_PLANS)),
                    )
                )
            )
            .scalars()
            .all()
        )
        if not users:
            return {"scholarships_due": len(scholarships), "users_notified": 0, "alerts_sent": 0}

        # Bulk-load every user's tracked scholarship ids in one query, then
        # bucket in Python. Replaces the per-user N+1 select.
        tracker_rows = (
            await session.execute(
                select(
                    ApplicationTrackerItem.user_id,
                    ApplicationTrackerItem.scholarship_id,
                ).where(
                    ApplicationTrackerItem.user_id.in_([u.id for u in users]),
                    ApplicationTrackerItem.scholarship_id.is_not(None),
                )
            )
        ).all()
        tracked_by_user: dict[str, set] = defaultdict(set)
        for user_id, scholarship_id in tracker_rows:
            tracked_by_user[str(user_id)].add(scholarship_id)

        users_notified = 0
        alerts_sent = 0
        for user in users:
            profile = user.student_profile
            target_countries = set(resolve_target_countries(profile))
            tracked_ids = tracked_by_user.get(str(user.id), set())

            if target_countries:
                candidates = (
                    s
                    for c in target_countries
                    for s in scholarships_by_country.get(c, [])
                )
            else:
                candidates = iter(scholarships)
            relevant = [s for s in candidates if s.id not in tracked_ids]
            if not relevant:
                continue

            titles = ", ".join(s.title for s in relevant[:3])
            body = (
                f"{len(relevant)} scholarship deadline(s) you qualify for close "
                f"within {ALERT_WINDOW_DAYS} days: {titles}. Add them to your "
                "tracker so you do not miss them."
            )
            await fan_out_for_plan(session, user, body)
            plan_key = (user.plan or "free").lower()
            channels = PLAN_CHANNELS.get(plan_key, ("email",))
            if channels:
                users_notified += 1
                alerts_sent += len(channels)

        logger.info(
            "priority_scholarship_alerts due=%d users_notified=%d alerts_sent=%d",
            len(scholarships),
            users_notified,
            alerts_sent,
        )
        return {
            "scholarships_due": len(scholarships),
            "users_notified": users_notified,
            "alerts_sent": alerts_sent,
        }


@celery_app.task(name="tasks.run_priority_scholarship_alerts")
def run_priority_scholarship_alerts() -> dict[str, int]:
    return asyncio.run(_run_priority_scholarship_alerts_async())
