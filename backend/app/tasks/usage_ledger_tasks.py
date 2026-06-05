"""Usage-ledger rollup + prune Celery beat task.

Mirrors ``kpi_tasks`` shape: a config-gated ``async def`` helper for direct
testability plus a thin ``@celery_app.task`` wrapper that ``asyncio.run``s it.
Folds detail rows older than the retention window into
``usage_ledger_monthly_summary`` then prunes them so ``month_to_date_pkr``
stops slowing as the append-only ledger grows.
"""
from __future__ import annotations

import asyncio

from app.core.config import settings
from app.core.database import async_session_factory
from app.services.usage import UsageLedgerMaintenanceService
from app.tasks.celery_app import celery_app


async def _run_usage_ledger_rollup_async() -> dict[str, int | bool]:
    if not settings.USAGE_LEDGER_ROLLUP_ENABLED:
        return {
            "enabled": False,
            "retention_months": settings.USAGE_LEDGER_RETENTION_MONTHS,
            "periods_rolled_up": 0,
            "rows_pruned": 0,
        }

    async with async_session_factory() as session:
        service = UsageLedgerMaintenanceService(session)
        counts = await service.rollup_and_prune(
            retention_months=settings.USAGE_LEDGER_RETENTION_MONTHS,
        )
        await session.commit()
        return {
            "enabled": True,
            "retention_months": settings.USAGE_LEDGER_RETENTION_MONTHS,
            **counts,
        }


@celery_app.task(name="tasks.run_usage_ledger_rollup")
def run_usage_ledger_rollup() -> dict[str, int | bool]:
    return asyncio.run(_run_usage_ledger_rollup_async())
