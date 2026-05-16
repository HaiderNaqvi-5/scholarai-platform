"""Elite application strategy report route (PRD §0.6)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import DocumentCreateUser
from app.schemas.reports import StrategyReportRequest, StrategyReportResponse
from app.services.reports import StrategyReportService

router = APIRouter()


@router.post(
    "/strategy",
    response_model=StrategyReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_strategy_report(
    payload: StrategyReportRequest,
    current_user: DocumentCreateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StrategyReportResponse:
    """Generate a 30/60/90-day application strategy report (PRD §0.6).

    Gated to elite + institution plans — returns HTTP 402 otherwise. Persists
    the report as a DocumentRecord (type strategy_report).
    """
    service = StrategyReportService(db)
    return await service.generate(current_user, payload)
