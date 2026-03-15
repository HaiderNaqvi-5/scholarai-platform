from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas import StudentProfileResponse, StudentProfileUpsertRequest
from app.services.students import StudentService

router = APIRouter()


@router.get("", response_model=StudentProfileResponse)
async def get_profile(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentProfileResponse:
    service = StudentService(db)
    profile = await service.get_profile(current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )
    return StudentProfileResponse.model_validate(profile)


@router.put("", response_model=StudentProfileResponse)
async def upsert_profile(
    payload: StudentProfileUpsertRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentProfileResponse:
    service = StudentService(db)
    profile = await service.upsert_profile(current_user.id, payload)
    return StudentProfileResponse.model_validate(profile)
