from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DocumentKPISnapshot,
    InterviewKPISnapshot,
    RecommendationKPISnapshot,
)
from app.schemas.analytics import KPISnapshotTrendItem


class KPISnapshotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_recommendation_snapshot(
        self,
        *,
        user_id: uuid.UUID,
        policy_version: str,
        kpi_passed: bool,
        metrics_payload: list[dict],
        gates_payload: list[dict],
    ) -> None:
        snapshot = RecommendationKPISnapshot(
            user_id=user_id,
            policy_version=policy_version,
            kpi_passed=kpi_passed,
            metrics_payload=metrics_payload,
            gates_payload=gates_payload,
        )
        self.db.add(snapshot)
        await self.db.flush()

    async def record_document_snapshot(
        self,
        *,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        policy_version: str,
        kpi_passed: bool,
        metrics_payload: dict,
        gate_payload: dict,
    ) -> None:
        snapshot = DocumentKPISnapshot(
            user_id=user_id,
            document_id=document_id,
            policy_version=policy_version,
            kpi_passed=kpi_passed,
            metrics_payload=metrics_payload,
            gate_payload=gate_payload,
        )
        self.db.add(snapshot)
        await self.db.flush()

    async def record_interview_snapshot(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        policy_version: str,
        kpi_passed: bool,
        metrics_payload: dict,
        gate_payload: dict,
    ) -> None:
        snapshot = InterviewKPISnapshot(
            user_id=user_id,
            session_id=session_id,
            policy_version=policy_version,
            kpi_passed=kpi_passed,
            metrics_payload=metrics_payload,
            gate_payload=gate_payload,
        )
        self.db.add(snapshot)
        await self.db.flush()

    async def recommendation_trends(self) -> list[KPISnapshotTrendItem]:
        return await self._trend_items(RecommendationKPISnapshot, "recommendation")

    async def document_trends(self) -> list[KPISnapshotTrendItem]:
        return await self._trend_items(DocumentKPISnapshot, "document")

    async def interview_trends(self) -> list[KPISnapshotTrendItem]:
        return await self._trend_items(InterviewKPISnapshot, "interview")

    async def _trend_items(self, model: type, metric_domain: str) -> list[KPISnapshotTrendItem]:
        total_count = func.count(model.id)
        passed_count = func.sum(case((model.kpi_passed.is_(True), 1), else_=0))

        result = await self.db.execute(
            select(
                model.policy_version,
                total_count.label("total"),
                passed_count.label("passed"),
            )
            .group_by(model.policy_version)
            .order_by(model.policy_version)
        )

        items: list[KPISnapshotTrendItem] = []
        for policy_version, total, passed in result.all():
            total_int = int(total or 0)
            passed_int = int(passed or 0)
            failed_int = max(total_int - passed_int, 0)
            pass_rate = round((passed_int / total_int), 4) if total_int else 0.0
            items.append(
                KPISnapshotTrendItem(
                    metric_domain=metric_domain,
                    policy_version=policy_version,
                    total_snapshots=total_int,
                    passed_snapshots=passed_int,
                    failed_snapshots=failed_int,
                    pass_rate=pass_rate,
                )
            )

        return items

    async def alert_messages(
        self,
        *,
        lookback_days: int,
        min_snapshots_per_domain: int,
        recommendation_pass_rate_min: float,
        document_pass_rate_min: float,
        interview_pass_rate_min: float,
    ) -> list[str]:
        lookback_cutoff = datetime.now(timezone.utc) - timedelta(days=max(lookback_days, 1))

        recommendation_alert = await self._domain_alert_message(
            model=RecommendationKPISnapshot,
            metric_domain="recommendation",
            lookback_cutoff=lookback_cutoff,
            min_snapshots=min_snapshots_per_domain,
            pass_rate_min=recommendation_pass_rate_min,
        )
        document_alert = await self._domain_alert_message(
            model=DocumentKPISnapshot,
            metric_domain="document",
            lookback_cutoff=lookback_cutoff,
            min_snapshots=min_snapshots_per_domain,
            pass_rate_min=document_pass_rate_min,
        )
        interview_alert = await self._domain_alert_message(
            model=InterviewKPISnapshot,
            metric_domain="interview",
            lookback_cutoff=lookback_cutoff,
            min_snapshots=min_snapshots_per_domain,
            pass_rate_min=interview_pass_rate_min,
        )

        alerts = [recommendation_alert, document_alert, interview_alert]
        return [alert for alert in alerts if alert is not None]

    async def _domain_alert_message(
        self,
        *,
        model: type,
        metric_domain: str,
        lookback_cutoff: datetime,
        min_snapshots: int,
        pass_rate_min: float,
    ) -> str | None:
        total_count = func.count(model.id)
        passed_count = func.sum(case((model.kpi_passed.is_(True), 1), else_=0))

        result = await self.db.execute(
            select(
                total_count.label("total"),
                passed_count.label("passed"),
            ).where(model.created_at >= lookback_cutoff)
        )
        row = result.one_or_none()
        if row is None:
            return None

        total_int = int(row.total or 0)
        passed_int = int(row.passed or 0)
        if total_int < max(min_snapshots, 1):
            return None

        pass_rate = passed_int / total_int if total_int else 0.0
        if pass_rate >= pass_rate_min:
            return None

        return (
            f"{metric_domain} KPI pass rate degraded: {pass_rate:.2%} over last "
            f"{total_int} snapshots (threshold {pass_rate_min:.2%})."
        )

    async def purge_snapshots_older_than(self, *, retention_days: int) -> dict[str, int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(retention_days, 1))

        recommendation_deleted = await self._delete_older_than(
            model=RecommendationKPISnapshot,
            cutoff=cutoff,
        )
        document_deleted = await self._delete_older_than(
            model=DocumentKPISnapshot,
            cutoff=cutoff,
        )
        interview_deleted = await self._delete_older_than(
            model=InterviewKPISnapshot,
            cutoff=cutoff,
        )

        total_deleted = recommendation_deleted + document_deleted + interview_deleted
        return {
            "recommendation_deleted": recommendation_deleted,
            "document_deleted": document_deleted,
            "interview_deleted": interview_deleted,
            "total_deleted": total_deleted,
        }

    async def _delete_older_than(self, *, model: type, cutoff: datetime) -> int:
        ids_result = await self.db.execute(select(model.id).where(model.created_at < cutoff))
        ids = list(ids_result.scalars().all())
        if not ids:
            return 0

        for snapshot_id in ids:
            snapshot = await self.db.get(model, snapshot_id)
            if snapshot is not None:
                await self.db.delete(snapshot)

        await self.db.flush()
        return len(ids)
