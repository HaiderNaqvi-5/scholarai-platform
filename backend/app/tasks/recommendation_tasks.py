from __future__ import annotations

import asyncio
import logging
import threading

import redis.asyncio as redis

from app.core.config import settings
from app.core.database import async_session_factory
from app.services.recommendations.embedding_refresh import (
    PublishedScholarshipEmbeddingRefresher,
)
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Dedup guard for the admin-triggered embedding refresh. A SETNX lock stops
# two concurrent ``POST /recommendations/refresh-embeddings`` enqueues from
# double-embedding every published scholarship. TTL is the lock's own
# safety net: if a worker dies mid-run the key expires and a later enqueue
# can re-acquire. Mirrors scraper_tasks' recent-run skip contract
# ({"status": "skipped", "reason": "recent_run_present"}).
_EMBEDDING_REFRESH_LOCK_KEY = "recommendation:embedding_refresh:lock"
EMBEDDING_REFRESH_LOCK_TTL_SECONDS = 30 * 60
_redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


@celery_app.task(name="tasks.recommendation_foundation_ping")
def recommendation_foundation_ping() -> dict[str, str]:
    return {
        "status": "ready",
        "message": "Celery foundation is active. Recommendation batch jobs remain deferred.",
    }


async def _run_embedding_refresh(
    limit: int | None = None,
) -> dict[str, int | bool | str]:
    try:
        acquired = await _redis_client.set(
            _EMBEDDING_REFRESH_LOCK_KEY,
            "1",
            nx=True,
            ex=EMBEDDING_REFRESH_LOCK_TTL_SECONDS,
        )
    except redis.RedisError as exc:  # fail-open: never block refresh on Redis outage
        logger.warning("Embedding-refresh lock unavailable, proceeding: %s", exc)
        acquired = True

    if not acquired:
        logger.info("embedding_refresh_skip reason=recent_run_present")
        return {"status": "skipped", "reason": "recent_run_present"}

    try:
        async with async_session_factory() as session:
            refresher = PublishedScholarshipEmbeddingRefresher(session)
            return await refresher.refresh_published_scholarships(limit=limit)
    finally:
        try:
            await _redis_client.delete(_EMBEDDING_REFRESH_LOCK_KEY)
        except redis.RedisError as exc:
            logger.warning("Embedding-refresh lock release failed: %s", exc)


def _run_coro_sync(coro):
    """
    Run an async coroutine from sync code.

    Celery workers call this task in a normal sync context (no running loop),
    while some unit tests invoke it from an active event loop thread.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, int | bool] = {}
    error: Exception | None = None

    def runner() -> None:
        nonlocal error
        try:
            result["value"] = asyncio.run(coro)
        except Exception as exc:  # pragma: no cover - defensive bridge
            error = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if error is not None:
        raise error
    return result["value"]


@celery_app.task(name="tasks.refresh_published_scholarship_embeddings")
def refresh_published_scholarship_embeddings(
    limit: int | None = None,
) -> dict[str, int | bool | str]:
    return _run_coro_sync(_run_embedding_refresh(limit=limit))
