import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    CurrentUser,
    InterviewCreateUser,
    InterviewReadUser,
    InterviewRespondUser,
)
from app.schemas import (
    InterviewAnswerRequest,
    InterviewCoachingAnalyticsResponse,
    InterviewCurrentQuestionResponse,
    InterviewSessionStartRequest,
    InterviewSessionSummaryResponse,
)
from app.schemas.visa_interview import (
    VisaInterviewAnswerRequest,
    VisaInterviewAnswerResponse,
    VisaInterviewSessionSummary,
    VisaInterviewStartRequest,
    VisaInterviewStartResponse,
)
from app.services.interview import InterviewSessionService
from app.services.visa_interview import VisaInterviewService

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


# ----------------------------------------------------------------------
# Pakistan-pivot visa interview simulator (Feature 8, PRD §8)
# ----------------------------------------------------------------------


@router.post(
    "/visa/start",
    response_model=VisaInterviewStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_visa_interview(
    payload: VisaInterviewStartRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisaInterviewStartResponse:
    service = VisaInterviewService(db)
    try:
        return await service.start(current_user, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/visa/{session_id}/answer",
    response_model=VisaInterviewAnswerResponse,
)
async def submit_visa_answer(
    session_id: uuid.UUID,
    payload: VisaInterviewAnswerRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisaInterviewAnswerResponse:
    service = VisaInterviewService(db)
    try:
        return await service.answer(current_user, session_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/visa/{session_id}/summary",
    response_model=VisaInterviewSessionSummary,
)
async def get_visa_session_summary(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisaInterviewSessionSummary:
    service = VisaInterviewService(db)
    try:
        return await service.summary(current_user, session_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{session_id}/responses", response_model=InterviewSessionSummaryResponse)
async def submit_interview_response(
    session_id: uuid.UUID,
    payload: InterviewAnswerRequest,
    current_user: InterviewRespondUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewSessionSummaryResponse:
    service = InterviewSessionService(db)
    return await service.submit_answer(current_user.id, session_id, payload)
