"""
Celery tasks for ScholarAI.

Tasks:
  - run_full_scrape       : Playwright-based multi-source scholarship scraper
  - compute_match_scores  : Recalculate recommendations for a single student profile
  - recompute_all_scores  : Batch recompute for all profiles (scheduled nightly)
  - generate_sop_task     : Async SOPService call for long generations
"""
import uuid
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


# ── Scraper ───────────────────────────────────────────────────────────────────

@shared_task(bind=True, name="tasks.run_full_scrape", max_retries=2, default_retry_delay=120)
def run_full_scrape(self):
    """Run Playwright scrapers for all configured scholarship sources.

    Each source is scraped sequentially; errors per-source are caught and
    logged without aborting other sources.
    """
    import asyncio
    from app.services.scraper_service import ScraperService

    logger.info("Starting full scholarship scrape run")

    async def _run():
        from app.core.database import async_session_factory
        async with async_session_factory() as db:
            svc = ScraperService(db)
            results = await svc.run_all()
            return results

    try:
        results = asyncio.run(_run())
        logger.info(f"Scrape complete: {results}")
        return results
    except Exception as exc:
        logger.exception("Scrape task failed")
        raise self.retry(exc=exc)


# ── Recommendation engine ─────────────────────────────────────────────────────

@shared_task(bind=True, name="tasks.compute_match_scores", max_retries=3, default_retry_delay=30)
def compute_match_scores(self, student_profile_id: str):
    """Compute and persist match scores for a single student profile."""
    import asyncio
    from app.services.recommendation_service import RecommendationService
    from app.models.models import StudentProfile

    async def _run():
        from app.core.database import async_session_factory
        from sqlalchemy import select

        async with async_session_factory() as db:
            result = await db.execute(
                select(StudentProfile).where(StudentProfile.id == uuid.UUID(student_profile_id))
            )
            profile = result.scalar_one_or_none()
            if not profile:
                logger.warning(f"StudentProfile {student_profile_id} not found")
                return 0
            svc = RecommendationService(db)
            count = await svc.compute_and_store(profile)
            logger.info(f"Wrote {count} match scores for profile {student_profile_id}")
            return count

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception(f"compute_match_scores failed for {student_profile_id}")
        raise self.retry(exc=exc)


@shared_task(name="tasks.recompute_all_scores")
def recompute_all_scores():
    """Nightly batch: recompute scores for every student profile."""
    import asyncio

    async def _run():
        from app.core.database import async_session_factory
        from app.models.models import StudentProfile
        from sqlalchemy import select

        async with async_session_factory() as db:
            result = await db.execute(select(StudentProfile.id))
            profile_ids = [str(row[0]) for row in result.fetchall()]

        # Dispatch individual Celery tasks per student
        for pid in profile_ids:
            compute_match_scores.delay(pid)

        logger.info(f"Dispatched {len(profile_ids)} score computation tasks")
        return len(profile_ids)

    return asyncio.run(_run())


# ── SOP generation ────────────────────────────────────────────────────────────

@shared_task(bind=True, name="tasks.generate_sop", max_retries=2, default_retry_delay=60)
def generate_sop_task(self, student_profile_id: str, scholarship_id: str, additional_context: str = ""):
    """Generate SOP for a student+scholarship pair. Result stored in cache via Redis."""
    import asyncio
    from app.services.sop_service import SopService

    async def _run():
        from app.core.database import async_session_factory
        from app.models.models import StudentProfile, Scholarship
        from sqlalchemy import select

        async with async_session_factory() as db:
            profile_result = await db.execute(
                select(StudentProfile).where(StudentProfile.id == uuid.UUID(student_profile_id))
            )
            profile = profile_result.scalar_one_or_none()

            sch_result = await db.execute(
                select(Scholarship).where(Scholarship.id == uuid.UUID(scholarship_id))
            )
            scholarship = sch_result.scalar_one_or_none()

            if not profile or not scholarship:
                return {"error": "Profile or scholarship not found"}

            svc = SopService()
            result = await svc.generate(profile, scholarship, additional_context)
            return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("SOP generation task failed")
        raise self.retry(exc=exc)
