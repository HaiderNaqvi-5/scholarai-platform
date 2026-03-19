from __future__ import annotations

import asyncio
import threading

from app.core.database import async_session_factory
from app.services.recommendations.embedding_refresh import (
    PublishedScholarshipEmbeddingRefresher,
)
from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.recommendation_foundation_ping")
def recommendation_foundation_ping() -> dict[str, str]:
    return {
        "status": "ready",
        "message": "Celery foundation is active. Recommendation batch jobs remain deferred.",
    }


async def _run_embedding_refresh(limit: int | None = None) -> dict[str, int | bool]:
    async with async_session_factory() as session:
        refresher = PublishedScholarshipEmbeddingRefresher(session)
        return await refresher.refresh_published_scholarships(limit=limit)


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
) -> dict[str, int | bool]:
    return _run_coro_sync(_run_embedding_refresh(limit=limit))
