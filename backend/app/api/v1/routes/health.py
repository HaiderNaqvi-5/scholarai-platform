from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthResponse
from app.services.kpi_snapshot_service import KPISnapshotService

router = APIRouter()

@router.get("", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check the health of the API and its database connection.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    kpi_alerts: list[str] = []
    if settings.KPI_OBSERVABILITY_ENABLED and db_status == "ok":
        snapshot_service = KPISnapshotService(db)
        kpi_alerts = await snapshot_service.alert_messages(
            lookback_days=settings.KPI_HEALTH_LOOKBACK_DAYS,
            min_snapshots_per_domain=settings.KPI_ALERT_MIN_SNAPSHOTS_PER_DOMAIN,
            recommendation_pass_rate_min=settings.KPI_ALERT_RECOMMENDATION_PASS_RATE_MIN,
            document_pass_rate_min=settings.KPI_ALERT_DOCUMENT_PASS_RATE_MIN,
            interview_pass_rate_min=settings.KPI_ALERT_INTERVIEW_PASS_RATE_MIN,
        )

    return HealthResponse(
        status="healthy" if db_status == "ok" and not kpi_alerts else "degraded",
        version=settings.APP_VERSION,
        database=db_status,
        kpi_alerts=kpi_alerts,
    )
