"""
AI-powered routes: SOP generation and Mock Interview coaching.
"""
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models.models import StudentProfile, Scholarship
from app.services.sop_service import SopService
from app.services.interview_service import InterviewService

router = APIRouter()


# ── Shared helper ─────────────────────────────────────────────────────────────

async def _get_profile_or_403(current_user, db: AsyncSession) -> StudentProfile:
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete your profile to access AI features",
        )
    return profile


async def _get_scholarship_or_404(scholarship_id: uuid.UUID, db: AsyncSession) -> Scholarship:
    result = await db.execute(select(Scholarship).where(Scholarship.id == scholarship_id))
    scholarship = result.scalar_one_or_none()
    if not scholarship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship not found")
    return scholarship


# ── SOP Routes ────────────────────────────────────────────────────────────────

class SopGenerateRequest(BaseModel):
    scholarship_id: uuid.UUID
    additional_context: str = Field("", max_length=2000)


class SopImproveRequest(BaseModel):
    current_sop: str = Field(..., min_length=100, max_length=8000)
    feedback_focus: Optional[str] = Field(None, max_length=200)


@router.post("/sop/generate")
async def generate_sop(
    payload: SopGenerateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate a tailored Statement of Purpose using GPT-4o."""
    profile     = await _get_profile_or_403(current_user, db)
    scholarship = await _get_scholarship_or_404(payload.scholarship_id, db)
    svc = SopService()
    result = await svc.generate(profile, scholarship, payload.additional_context)
    return result


@router.post("/sop/improve")
async def improve_sop(
    payload: SopImproveRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Improve an existing SOP with targeted AI feedback."""
    await _get_profile_or_403(current_user, db)  # ensure user has profile
    svc = SopService()
    result = await svc.improve(payload.current_sop, payload.feedback_focus)
    return result


# ── Interview Routes ──────────────────────────────────────────────────────────

class InterviewQuestionsRequest(BaseModel):
    scholarship_id: uuid.UUID
    question_count: int = Field(5, ge=1, le=10)
    focus_areas: Optional[List[str]] = None


class InterviewEvaluateRequest(BaseModel):
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=10, max_length=5000)
    scholarship_id: Optional[uuid.UUID] = None


class SessionQAPair(BaseModel):
    question: str
    answer: str


class SessionEvaluateRequest(BaseModel):
    qa_pairs: List[SessionQAPair] = Field(..., min_length=1, max_length=10)


@router.post("/interview/questions")
async def generate_interview_questions(
    payload: InterviewQuestionsRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate contextual mock interview questions."""
    profile     = await _get_profile_or_403(current_user, db)
    scholarship = await _get_scholarship_or_404(payload.scholarship_id, db)
    svc = InterviewService()
    questions = await svc.generate_questions(
        profile, scholarship,
        question_count=payload.question_count,
        focus_areas=payload.focus_areas,
    )
    return {"questions": questions}


@router.post("/interview/evaluate")
async def evaluate_interview_answer(
    payload: InterviewEvaluateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Score a single mock interview answer with detailed feedback."""
    profile = await _get_profile_or_403(current_user, db)
    scholarship = None
    if payload.scholarship_id:
        scholarship = await _get_scholarship_or_404(payload.scholarship_id, db)
    svc = InterviewService()
    result = await svc.evaluate_answer(
        question=payload.question,
        answer=payload.answer,
        profile=profile,
        scholarship=scholarship,
    )
    return result


@router.post("/interview/session")
async def evaluate_interview_session(
    payload: SessionEvaluateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Holistic evaluation of a full mock interview session."""
    await _get_profile_or_403(current_user, db)
    svc = InterviewService()
    result = await svc.evaluate_session([
        {"question": qa.question, "answer": qa.answer}
        for qa in payload.qa_pairs
    ])
    return result
