"""B2B share REST surface (Feature 9.5, PRD §9.5).

Owner / institution role required. Every share path enforces the consent
gate (b2b_share_consent must be true) AND the DPA gate
(institutions.dpa_signed_at must be set).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.core.plan_guard import has_plan_at_least
from app.models import User
from app.schemas.privacy import B2BShareRequest, B2BShareResponse
from app.services.privacy import B2BShareService


router = APIRouter()


@router.post("/share", response_model=B2BShareResponse, status_code=status.HTTP_201_CREATED)
async def share_student_lead(
    payload: B2BShareRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> B2BShareResponse:
    # Caller must be institution-tier or owner. Free / Pro / Elite cannot.
    if not has_plan_at_least(current_user, "institution"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "institution_plan_required",
                "message": "Only institution-tier accounts can share student leads.",
            },
        )

    target = await db.get(User, payload.target_user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    # P1-2 IDOR fix: target must belong to the caller's institution.
    # A null institution_id on the caller means they are not scoped to any
    # institution and therefore cannot share ANY student (platform/owner
    # accounts must use an institution-scoped account for B2B sharing).
    caller_institution = getattr(current_user, "institution_id", None)
    if caller_institution is None or target.institution_id != caller_institution:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "cross_institution_share_forbidden",
                "message": "Target student is not part of your institution.",
            },
        )

    service = B2BShareService(db)
    lead = await service.share_profile(
        target_user=target,
        university_id=payload.university_id,
        share_reason=payload.share_reason,
        shared_with_email=str(payload.shared_with_email) if payload.shared_with_email else None,
        institution_id=payload.institution_id,
    )
    return B2BShareResponse(
        id=lead.id,
        target_user_id=lead.user_id,
        university_id=lead.university_id,
        share_reason=lead.share_reason,
        shared_at=lead.shared_at,
        consent_audit_log_id=lead.consent_audit_log_id,
    )
