"""
Admin-only routes: scholarship CRUD, scraper control, audit log.
"""
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import AdminUser
from app.models.models import Scholarship, ScraperRun, AuditLog
from app.api.v1.schemas import (
    AdminScholarshipCreate, AdminScholarshipUpdate, ScholarshipResponse,
    ScraperRunResponse, AuditLogResponse, PaginatedResponse,
)

router = APIRouter()


# ── Scholarship CRUD ──────────────────────────────────────────────────────────

@router.post("/scholarships", response_model=ScholarshipResponse, status_code=status.HTTP_201_CREATED)
async def create_scholarship(
    payload: AdminScholarshipCreate,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    scholarship = Scholarship(**payload.model_dump())
    db.add(scholarship)
    await db.commit()
    await db.refresh(scholarship)
    return scholarship


@router.patch("/scholarships/{scholarship_id}", response_model=ScholarshipResponse)
async def update_scholarship(
    scholarship_id: uuid.UUID,
    payload: AdminScholarshipUpdate,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Scholarship).where(Scholarship.id == scholarship_id))
    scholarship = result.scalar_one_or_none()
    if not scholarship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scholarship, field, value)

    await db.commit()
    await db.refresh(scholarship)
    return scholarship


@router.delete("/scholarships/{scholarship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scholarship(
    scholarship_id: uuid.UUID,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Scholarship).where(Scholarship.id == scholarship_id))
    scholarship = result.scalar_one_or_none()
    if not scholarship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship not found")

    await db.delete(scholarship)
    await db.commit()


# ── Scraper Control ───────────────────────────────────────────────────────────

@router.get("/scraper/runs", response_model=List[ScraperRunResponse])
async def list_scraper_runs(
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(ScraperRun).order_by(ScraperRun.started_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.post("/scraper/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scraper(admin: AdminUser):
    """Enqueue a full Playwright scraper run via Celery."""
    from app.tasks.scraper_tasks import run_full_scrape
    task = run_full_scrape.delay()
    return {"task_id": task.id, "status": "queued"}


# ── Audit Log ─────────────────────────────────────────────────────────────────

@router.get("/audit-logs", response_model=PaginatedResponse)
async def get_audit_logs(
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    count_result = await db.execute(select(func.count()).select_from(AuditLog))
    total = count_result.scalar_one()

    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AuditLogResponse.model_validate(l) for l in logs],
    )


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_platform_stats(
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Quick platform health stats for admin dashboard."""
    from app.models.models import User, StudentProfile, Application

    stats = {}
    for model, key in [
        (User, "total_users"),
        (StudentProfile, "total_profiles"),
        (Scholarship, "total_scholarships"),
        (Application, "total_applications"),
    ]:
        result = await db.execute(select(func.count()).select_from(model))
        stats[key] = result.scalar_one()

    return stats
