"""
Celery tasks for ScholarAI recommendation and AI workloads.
"""

import logging
import uuid

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="tasks.compute_match_scores", max_retries=3, default_retry_delay=30)
def compute_match_scores(self, student_profile_id: str):
    """Compute and persist match scores for a single student profile."""
    import asyncio

    from app.models.models import StudentProfile
    from app.services.recommendation_service import RecommendationService

    async def _run():
        from sqlalchemy import select

        from app.core.database import async_session_factory

        async with async_session_factory() as db:
            result = await db.execute(
                select(StudentProfile).where(StudentProfile.id == uuid.UUID(student_profile_id))
            )
            profile = result.scalar_one_or_none()
            if not profile:
                logger.warning("StudentProfile %s not found", student_profile_id)
                return 0

            svc = RecommendationService(db)
            count = await svc.compute_and_store(profile)
            logger.info("Wrote %s match scores for profile %s", count, student_profile_id)
            return count

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("compute_match_scores failed for %s", student_profile_id)
        raise self.retry(exc=exc)


@shared_task(name="tasks.recompute_all_scores")
def recompute_all_scores():
    """Nightly batch: recompute scores for every student profile."""
    import asyncio

    async def _run():
        from sqlalchemy import select

        from app.core.database import async_session_factory
        from app.models.models import StudentProfile

        async with async_session_factory() as db:
            result = await db.execute(select(StudentProfile.id))
            profile_ids = [str(row[0]) for row in result.fetchall()]

        for profile_id in profile_ids:
            compute_match_scores.delay(profile_id)

        logger.info("Dispatched %s score computation tasks", len(profile_ids))
        return len(profile_ids)

    return asyncio.run(_run())


@shared_task(bind=True, name="tasks.generate_sop", max_retries=2, default_retry_delay=60)
def generate_sop_task(self, student_profile_id: str, scholarship_id: str, additional_context: str = ""):
    """Generate an SOP draft for a student/scholarship pair."""
    import asyncio

    from app.services.sop_service import SopService

    async def _run():
        from sqlalchemy import select

        from app.core.database import async_session_factory
        from app.models.models import Scholarship, StudentProfile

        async with async_session_factory() as db:
            profile_result = await db.execute(
                select(StudentProfile).where(StudentProfile.id == uuid.UUID(student_profile_id))
            )
            profile = profile_result.scalar_one_or_none()

            scholarship_result = await db.execute(
                select(Scholarship).where(Scholarship.id == uuid.UUID(scholarship_id))
            )
            scholarship = scholarship_result.scalar_one_or_none()

            if not profile or not scholarship:
                return {"error": "Profile or scholarship not found"}

            svc = SopService()
            return await svc.generate(profile, scholarship, additional_context)

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("SOP generation task failed for profile %s", student_profile_id)
        raise self.retry(exc=exc)
