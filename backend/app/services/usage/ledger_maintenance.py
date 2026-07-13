"""Usage-ledger rollup, prune, and admin reset.

``usage_ledger`` is append-only; left alone it grows unbounded and the
month-to-date burn-cap aggregate slows. ``rollup_and_prune`` folds every
period older than the retention window into ``usage_ledger_monthly_summary``
(one row per user/period) then deletes the rolled detail rows. ``reset_user``
is the admin escape hatch that zeroes a user's current-period spend.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.burn_cap import _period
from app.models import UsageLedger, UsageLedgerMonthlySummary


def _cutoff_period(retention_months: int) -> str:
    """`YYYYMM` of the oldest period kept in detail (inclusive).

    Periods strictly less than this stamp get rolled up + pruned.
    """
    now = datetime.now(timezone.utc)
    total = now.year * 12 + (now.month - 1) - retention_months
    year, month = divmod(total, 12)
    return f"{year:04d}{month + 1:02d}"


class UsageLedgerMaintenanceService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def rollup_and_prune(self, *, retention_months: int) -> dict[str, int]:
        cutoff = _cutoff_period(retention_months)
        agg = await self._db.execute(
            select(
                UsageLedger.user_id,
                UsageLedger.period_yyyymm,
                func.coalesce(func.sum(UsageLedger.cost_pkr_micro), 0).label("cost"),
                func.count().label("rows"),
            )
            .where(UsageLedger.period_yyyymm < cutoff)
            .group_by(UsageLedger.user_id, UsageLedger.period_yyyymm)
        )
        rows = agg.all()
        for user_id, period, cost, count in rows:
            stmt = (
                pg_insert(UsageLedgerMonthlySummary)
                .values(
                    user_id=user_id,
                    period_yyyymm=period,
                    cost_pkr_micro=int(cost),
                    row_count=int(count),
                )
                .on_conflict_do_update(
                    constraint="uq_usage_summary_user_period",
                    set_={
                        "cost_pkr_micro": int(cost),
                        "row_count": int(count),
                    },
                )
            )
            await self._db.execute(stmt)
        pruned = await self._db.execute(
            delete(UsageLedger).where(UsageLedger.period_yyyymm < cutoff)
        )
        return {
            "periods_rolled_up": len(rows),
            "rows_pruned": int(pruned.rowcount or 0),
        }

    async def reset_user(self, user_id) -> int:
        """Delete the user's current-period detail rows. Returns rows removed."""
        result = await self._db.execute(
            delete(UsageLedger).where(
                UsageLedger.user_id == user_id,
                UsageLedger.period_yyyymm == _period(),
            )
        )
        return int(result.rowcount or 0)
