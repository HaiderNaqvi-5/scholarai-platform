import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import InterviewCreateUser, InterviewReadUser, InterviewRespondUser
from app.schemas import (
    InterviewAnswerRequest,
    InterviewCoachingAnalyticsResponse,
    InterviewCurrentQuestionResponse,
    InterviewSessionStartRequest,
    InterviewSessionSummaryResponse,
)
from app.services.interview import InterviewSessionService

router = APIRouter()


@router.post("", response_model=InterviewSessionSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_interview_session(
    payload: InterviewSessionStartRequest,
    current_user: InterviewCreateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewSessionSummaryResponse:
    service = InterviewSessionService(db)
    return await service.start_session(
        current_user.id,
        practice_mode=payload.practice_mode,
        scholarship_id=payload.scholarship_id,
    )


@router.get("/coaching-analytics", response_model=InterviewCoachingAnalyticsResponse)
async def get_interview_coaching_analytics(
    current_user: InterviewReadUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewCoachingAnalyticsResponse:
    service = InterviewSessionService(db)
    return await service.get_coaching_analytics(current_user.id)


@router.get("/{session_id}", response_model=InterviewSessionSummaryResponse)
async def get_interview_session(
    session_id: uuid.UUID,
    current_user: InterviewReadUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewSessionSummaryResponse:
    service = InterviewSessionService(db)
    return await service.get_session(current_user.id, session_id)


@router.get("/{session_id}/question", response_model=InterviewCurrentQuestionResponse)
async def get_interview_question(
    session_id: uuid.UUID,
    current_user: InterviewReadUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewCurrentQuestionResponse:
    service = InterviewSessionService(db)
    return await service.get_current_question(current_user.id, session_id)


@router.post("/{session_id}/responses", response_model=InterviewSessionSummaryResponse)
async def submit_interview_response(
    session_id: uuid.UUID,
    payload: InterviewAnswerRequest,
    current_user: InterviewRespondUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewSessionSummaryResponse:
    service = InterviewSessionService(db)
    return await service.submit_answer(current_user.id, session_id, payload)
