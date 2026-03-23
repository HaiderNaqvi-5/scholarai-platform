from __future__ import annotations

import asyncio

from app.core.config import settings
from app.core.database import async_session_factory
from app.services.kpi_snapshot_service import KPISnapshotService
from app.tasks.celery_app import celery_app


async def _run_kpi_snapshot_retention_cleanup_async() -> dict[str, int | bool]:
    if not settings.KPI_SNAPSHOT_RETENTION_ENABLED:
        return {
            "enabled": False,
            "retention_days": settings.KPI_SNAPSHOT_RETENTION_DAYS,
            "recommendation_deleted": 0,
            "document_deleted": 0,
            "interview_deleted": 0,
            "total_deleted": 0,
        }

    async with async_session_factory() as session:
        snapshot_service = KPISnapshotService(session)
        deleted_counts = await snapshot_service.purge_snapshots_older_than(
            retention_days=settings.KPI_SNAPSHOT_RETENTION_DAYS,
        )
        await session.commit()

        return {
            "enabled": True,
            "retention_days": settings.KPI_SNAPSHOT_RETENTION_DAYS,
            **deleted_counts,
        }


@celery_app.task(name="tasks.run_kpi_snapshot_retention_cleanup")
def run_kpi_snapshot_retention_cleanup() -> dict[str, int | bool]:
    return asyncio.run(_run_kpi_snapshot_retention_cleanup_async())
