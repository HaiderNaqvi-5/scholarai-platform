"""
Admin analytics and system health endpoints.

Provides aggregate platform metrics for the admin dashboard:
user counts, scholarship stats, application statuses, and recent ingestion health.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminAuditUser, AdminUser
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

    # ── User counts (single GROUP BY role, bucketed in Python) ────────────
    student_roles = {UserRole.STUDENT, UserRole.ENDUSER_STUDENT}
    mentor_roles = {UserRole.MENTOR, UserRole.INTERNAL_USER}
    admin_roles = {UserRole.ADMIN, UserRole.DEV, UserRole.OWNER}

    role_counts = (
        await db.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
    ).all()

    total_users = 0
    student_count = 0
    mentor_count = 0
    admin_count = 0
    for role, count in role_counts:
        count = count or 0
        total_users += count
        if role in student_roles:
            student_count += count
        elif role in mentor_roles:
            mentor_count += count
        elif role in admin_roles:
            admin_count += count

    # ── Scholarship counts ────────────────────────────────────────────────
    total_scholarships = (
        await db.execute(select(func.count(Scholarship.id)))
    ).scalar() or 0

    # ── Application counts (total + submitted in one aggregate) ───────────
    application_totals = (
        await db.execute(
            select(
                func.count(Application.id),
                func.count(Application.id).filter(
                    Application.status == ApplicationStatus.SUBMITTED
                ),
            )
        )
    ).one()
    total_applications = application_totals[0] or 0
    submitted_applications = application_totals[1] or 0

    # ── Document counts ───────────────────────────────────────────────────
    total_documents = (
        await db.execute(select(func.count(DocumentRecord.id)))
    ).scalar() or 0

    # ── Interview session counts ──────────────────────────────────────────
    total_interview_sessions = (
        await db.execute(select(func.count(InterviewSession.id)))
    ).scalar() or 0

    # ── Ingestion health (total + failed in one aggregate) ───────────────
    ingestion_totals = (
        await db.execute(
            select(
                func.count(IngestionRun.id),
                func.count(IngestionRun.id).filter(
                    IngestionRun.status == IngestionRunStatus.FAILED
                ),
            )
        )
    ).one()
    total_runs = ingestion_totals[0] or 0
    failed_runs = ingestion_totals[1] or 0

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


@router.post("/usage-ledger/reset")
async def reset_usage_ledger(
    user_id: UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    """Admin: clear a user's current-period burn-cap spend (escape hatch)."""
    del current_user
    from app.services.usage import UsageLedgerMaintenanceService

    deleted = await UsageLedgerMaintenanceService(db).reset_user(user_id)
    await db.commit()
    return {"status": "reset", "user_id": str(user_id), "rows_deleted": deleted}
