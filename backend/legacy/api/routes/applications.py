"""
Application routes: apply to scholarships, list my applications, update status.
"""
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models.models import Application, Scholarship, StudentProfile
from app.api.v1.schemas import ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate

router = APIRouter()


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_scholarship(
    payload: ApplicationCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new scholarship application for the current student."""
    # Ensure student has a profile
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Complete your profile before applying",
        )

    # Ensure scholarship exists and is active
    sch_result = await db.execute(
        select(Scholarship).where(
            Scholarship.id == payload.scholarship_id,
            Scholarship.is_active == True,
        )
    )
    scholarship = sch_result.scalar_one_or_none()
    if not scholarship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship not found or inactive")

    # Prevent duplicate applications
    dup_result = await db.execute(
        select(Application).where(
            Application.student_id == profile.id,
            Application.scholarship_id == payload.scholarship_id,
        )
    )
    if dup_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this scholarship",
        )

    application = Application(
        student_id=profile.id,
        scholarship_id=payload.scholarship_id,
        status="draft",
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("", response_model=List[ApplicationResponse])
async def list_my_applications(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    application_status: str | None = Query(None, alias="status"),
):
    """List all applications for the current student."""
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        return []

    q = select(Application).where(Application.student_id == profile.id)
    if application_status:
        q = q.where(Application.status == application_status)

    result = await db.execute(q.order_by(Application.created_at.desc()))
    return result.scalars().all()


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID,
    payload: ApplicationStatusUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Student can move application from draft → submitted only."""
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.student_id == (profile.id if profile else None),
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Students may only set their own applications to "submitted"
    allowed_transitions = {"draft": ["submitted"]}
    if payload.status not in allowed_transitions.get(application.status, []):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot transition from '{application.status}' to '{payload.status}'",
        )

    application.status = payload.status
    await db.commit()
    await db.refresh(application)
    return application
