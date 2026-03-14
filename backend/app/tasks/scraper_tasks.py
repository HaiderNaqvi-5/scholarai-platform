"""
Scraper Celery tasks.

Tasks:
  - run_full_scrape: Run all scrapers across all sources. Triggered weekly via
    beat schedule (Sunday 03:00 UTC). Routed to the 'scraper' queue.

Each task creates an async event loop and delegates to ScraperService.
"""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.run_full_scrape", bind=True, max_retries=2)
def run_full_scrape(self) -> dict:
    """
    Entrypoint for full scholarship scrape.

    Creates a fresh DB session and runs all scrapers defined in
    ScraperService.run_all(). On failure, retries up to 2 times with
    exponential back-off.
    """
    try:
        return asyncio.run(_async_run_full_scrape())
    except Exception as exc:
        logger.exception("run_full_scrape failed, retrying")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


async def _async_run_full_scrape() -> dict:
    """Async implementation: opens DB session, delegates to ScraperService."""
    from app.core.database import AsyncSessionLocal
    from app.services.scraper_service import ScraperService

    async with AsyncSessionLocal() as db:
        service = ScraperService(db)
        stats = await service.run_all()
        logger.info("Scrape completed: %s", stats)
        return stats
