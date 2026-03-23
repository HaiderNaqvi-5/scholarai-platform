"""
Admin analytics and system health endpoints.

Provides aggregate platform metrics for the admin dashboard:
user counts, scholarship stats, application statuses, and recent ingestion health.
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminAuditUser
from app.models import (
    Application,
    ApplicationStatus,
    DocumentRecord,
    IngestionRun,
    IngestionRunStatus,
    InterviewSession,
    Scholarship,
    User,
    UserRole,
)
from app.schemas.analytics import PlatformAnalyticsResponse
from app.services.kpi_snapshot_service import KPISnapshotService

router = APIRouter()


@router.get("", response_model=PlatformAnalyticsResponse)
async def get_platform_analytics(
    current_user: AdminAuditUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlatformAnalyticsResponse:
    """Return aggregate platform metrics for the admin dashboard."""
    kpi_snapshot_service = KPISnapshotService(db)

    # ── User counts ───────────────────────────────────────────────────────
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    student_count = (
        await db.execute(
            select(func.count(User.id)).where(
                User.role.in_([UserRole.STUDENT, UserRole.ENDUSER_STUDENT])
            )
        )
    ).scalar() or 0
    mentor_count = (
        await db.execute(
            select(func.count(User.id)).where(
                User.role.in_([UserRole.MENTOR, UserRole.INTERNAL_USER])
            )
        )
    ).scalar() or 0
    admin_count = (
        await db.execute(
            select(func.count(User.id)).where(
                User.role.in_([UserRole.ADMIN, UserRole.DEV, UserRole.OWNER])
            )
        )
    ).scalar() or 0

    # ── Scholarship counts ────────────────────────────────────────────────
    total_scholarships = (
        await db.execute(select(func.count(Scholarship.id)))
    ).scalar() or 0

    # ── Application counts ────────────────────────────────────────────────
    total_applications = (
        await db.execute(select(func.count(Application.id)))
    ).scalar() or 0
    submitted_applications = (
        await db.execute(
            select(func.count(Application.id)).where(
                Application.status == ApplicationStatus.SUBMITTED
            )
        )
    ).scalar() or 0

    # ── Document counts ───────────────────────────────────────────────────
    total_documents = (
        await db.execute(select(func.count(DocumentRecord.id)))
    ).scalar() or 0

    # ── Interview session counts ──────────────────────────────────────────
    total_interview_sessions = (
        await db.execute(select(func.count(InterviewSession.id)))
    ).scalar() or 0

    # ── Ingestion health ──────────────────────────────────────────────────
    total_runs = (
        await db.execute(select(func.count(IngestionRun.id)))
    ).scalar() or 0
    failed_runs = (
        await db.execute(
            select(func.count(IngestionRun.id)).where(
                IngestionRun.status == IngestionRunStatus.FAILED
            )
        )
    ).scalar() or 0

    recommendation_trends = await kpi_snapshot_service.recommendation_trends()
    document_trends = await kpi_snapshot_service.document_trends()
    interview_trends = await kpi_snapshot_service.interview_trends()
    kpi_trends = recommendation_trends + document_trends + interview_trends

    return PlatformAnalyticsResponse(
        total_users=total_users,
        student_count=student_count,
        mentor_count=mentor_count,
        admin_count=admin_count,
        total_scholarships=total_scholarships,
        total_applications=total_applications,
        submitted_applications=submitted_applications,
        total_documents=total_documents,
        total_interview_sessions=total_interview_sessions,
        ingestion_runs_total=total_runs,
        ingestion_runs_failed=failed_runs,
        kpi_trends=kpi_trends,
    )
