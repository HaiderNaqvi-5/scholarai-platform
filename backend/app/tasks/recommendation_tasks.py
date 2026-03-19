from __future__ import annotations

import asyncio

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


@celery_app.task(name="tasks.refresh_published_scholarship_embeddings")
def refresh_published_scholarship_embeddings(
    limit: int | None = None,
) -> dict[str, int | bool]:
    return asyncio.run(_run_embedding_refresh(limit=limit))
