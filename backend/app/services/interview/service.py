import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    InterviewPracticeMode,
    InterviewResponse,
    InterviewSession,
    InterviewSessionStatus,
)
from app.schemas.interviews import (
    InterviewAnswerFeedback,
    InterviewAnswerRequest,
    InterviewCurrentQuestionResponse,
    InterviewSessionSummaryResponse,
)
from app.services.interview.scoring import InterviewScoringService
import os

GENERAL_QUESTION_SET = [
    "Tell us about yourself and what led you to pursue graduate study in data science or analytics.",
    "Describe a project or experience that shows how you solve problems under uncertainty.",
    "Why would you be a strong fit for a scholarship that values academic promise and future impact?",
]


class InterviewSessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scoring_service = InterviewScoringService()
        self.evaluator = None
        if os.environ.get("GOOGLE_API_KEY"):
            try:
                from app.services.interview.evaluator import InterviewEvaluator
                self.evaluator = InterviewEvaluator()
            except Exception as e:
                print(f"Failed to load AI Integrations: {e}")

    async def start_session(
        self,
        user_id: uuid.UUID,
        practice_mode: str = InterviewPracticeMode.GENERAL.value,
    ) -> InterviewSessionSummaryResponse:
        parsed_mode = self._parse_mode(practice_mode)
        session = InterviewSession(
            user_id=user_id,
            practice_mode=parsed_mode,
            status=InterviewSessionStatus.IN_PROGRESS,
            current_question_index=0,
            total_questions=len(GENERAL_QUESTION_SET),
            question_set=list(GENERAL_QUESTION_SET),
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        await self.db.flush()
        session = await self._load_session(user_id, session.id)
        return self._build_session_response(session)

    async def get_session(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> InterviewSessionSummaryResponse:
        session = await self._load_session(user_id, session_id)
        return self._build_session_response(session)

    async def get_current_question(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> InterviewCurrentQuestionResponse:
        session = await self._load_session(user_id, session_id)
        return self._build_current_question(session)

    async def submit_answer(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        payload: InterviewAnswerRequest,
    ) -> InterviewSessionSummaryResponse:
        session = await self._load_session(user_id, session_id)
        if session.status == InterviewSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interview session is already completed",
            )

        question_index = session.current_question_index
        if question_index >= session.total_questions:
            session.status = InterviewSessionStatus.COMPLETED
            session.completed_at = session.completed_at or datetime.now(timezone.utc)
            await self.db.flush()
            return self._build_session_response(session)

        existing_indexes = {response.question_index for response in session.responses}
        if question_index in existing_indexes:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Current question has already been answered",
            )

        question_text = session.question_set[question_index]
        
        feedback = None
        if self.evaluator:
            try:
                feedback = self.evaluator.evaluate(
                    question_index=question_index,
                    question_text=question_text,
                    audio_b64=payload.audio_b64,
                    text_answer=payload.answer_text,
                )
            except Exception as e:
                print(f"Gemini evaluation failed, falling back to rules: {e}")
        
        if not feedback:
            fallback_text = payload.answer_text or "The audio processing failed. This is a fallback."
            feedback = self.scoring_service.score_answer(
                question_index=question_index,
                question_text=question_text,
                answer_text=fallback_text,
            )

        response = InterviewResponse(
            session_id=session.id,
            question_index=question_index,
            question_text=question_text,
            answer_text=feedback.answer_text,
            score_payload=feedback.model_dump(),
            summary_feedback=feedback.summary_feedback,
        )
        self.db.add(response)

        session.current_question_index += 1
        if session.current_question_index >= session.total_questions:
            session.status = InterviewSessionStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc)
        else:
            session.status = InterviewSessionStatus.IN_PROGRESS

        await self.db.flush()
        await self.db.refresh(session)
        session = await self._load_session(user_id, session.id)
        return self._build_session_response(session)

    async def _load_session(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> InterviewSession:
        result = await self.db.execute(
            select(InterviewSession)
            .where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
            .options(selectinload(InterviewSession.responses))
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview session not found",
            )
        return session

    def _build_session_response(
        self,
        session: InterviewSession,
    ) -> InterviewSessionSummaryResponse:
        sorted_responses = sorted(session.responses, key=lambda item: item.question_index)
        response_items = [self._build_feedback(response) for response in sorted_responses]
        latest_feedback = response_items[-1] if response_items else None

        return InterviewSessionSummaryResponse(
            session_id=str(session.id),
            status=session.status.value,
            practice_mode=session.practice_mode.value,
            current_question_index=session.current_question_index,
            total_questions=session.total_questions,
            current_question=self._build_current_question(session),
            responses=response_items,
            latest_feedback=latest_feedback,
            started_at=session.started_at,
            completed_at=session.completed_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def _build_current_question(
        self,
        session: InterviewSession,
    ) -> InterviewCurrentQuestionResponse:
        question_text = None
        if session.status != InterviewSessionStatus.COMPLETED and session.current_question_index < len(
            session.question_set
        ):
            question_text = session.question_set[session.current_question_index]

        return InterviewCurrentQuestionResponse(
            session_id=str(session.id),
            status=session.status.value,
            practice_mode=session.practice_mode.value,
            question_index=min(session.current_question_index + 1, session.total_questions),
            total_questions=session.total_questions,
            question_text=question_text,
        )

    def _build_feedback(self, response: InterviewResponse) -> InterviewAnswerFeedback:
        payload = response.score_payload or {}
        return InterviewAnswerFeedback(
            question_index=payload.get("question_index", response.question_index),
            question_text=payload.get("question_text", response.question_text),
            answer_text=payload.get("answer_text", response.answer_text),
            overall_score=payload.get("overall_score", 0),
            overall_band=payload.get("overall_band", "developing"),
            scoring_mode=payload.get("scoring_mode", self.scoring_service.scoring_mode),
            summary_feedback=payload.get("summary_feedback", response.summary_feedback),
            strengths=list(payload.get("strengths", [])),
            improvement_prompts=list(payload.get("improvement_prompts", [])),
            dimensions=list(payload.get("dimensions", [])),
            limitation_notice=payload.get(
                "limitation_notice",
                "This is practice guidance only.",
            ),
            created_at=response.created_at,
        )

    def _parse_mode(self, value: str) -> InterviewPracticeMode:
        try:
            return InterviewPracticeMode(value.lower())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview practice mode must be 'general'",
            ) from exc
