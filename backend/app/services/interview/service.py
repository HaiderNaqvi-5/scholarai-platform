import os
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
    Scholarship,
)
from app.schemas.interviews import (
    InterviewAnswerFeedback,
    InterviewAnswerRequest,
    InterviewCoachingAnalyticsResponse,
    InterviewCoachingRecentSession,
    InterviewCurrentQuestionResponse,
    InterviewHistorySummary,
    InterviewProgressionGate,
    InterviewProgressionMetrics,
    InterviewSessionSummaryResponse,
    InterviewTrendSummary,
)
from app.services.documents.grounding import validate_scholarship_grounding
from app.services.kpi_policy import (
    get_interview_progression_policy_version,
    get_interview_progression_thresholds,
)
from app.services.kpi_snapshot_service import KPISnapshotService
from app.services.interview.bounded_guidance import (
    build_adaptive_question,
    build_history_summary,
    build_question_set,
    build_trend_summary,
    select_weakest_dimension,
)
from app.services.interview.scoring import InterviewScoringService


class InterviewSessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scoring_service = InterviewScoringService()
        self.kpi_snapshot_service = KPISnapshotService(db)
        self.evaluator = None
        if os.environ.get("GOOGLE_API_KEY"):
            try:
                from app.services.interview.evaluator import InterviewEvaluator

                self.evaluator = InterviewEvaluator()
            except Exception as exc:  # pragma: no cover
                print(f"Failed to load AI integrations: {exc}")


    async def start_session(
        self,
        user_id: uuid.UUID,
        practice_mode: str = InterviewPracticeMode.GENERAL.value,
        scholarship_id: str | uuid.UUID | None = None,
    ) -> InterviewSessionSummaryResponse:
        parsed_mode = self._parse_mode(practice_mode)
        grounded_scholarships = await self._resolve_grounding(scholarship_id)
        question_set = build_question_set(parsed_mode.value, grounded_scholarships)

        session = InterviewSession(
            user_id=user_id,
            practice_mode=parsed_mode,
            scholarship_id=grounded_scholarships[0].id if grounded_scholarships else None,
            status=InterviewSessionStatus.IN_PROGRESS,
            current_question_index=0,
            total_questions=len(question_set),
            question_set=question_set,
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

    async def get_coaching_analytics(
        self,
        user_id: uuid.UUID,
    ) -> InterviewCoachingAnalyticsResponse:
        result = await self.db.execute(
            select(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status == InterviewSessionStatus.COMPLETED,
            )
            .options(selectinload(InterviewSession.responses))
            .order_by(InterviewSession.updated_at.desc())
        )
        all_sessions = result.scalars().all()
        # Only include sessions that have at least one response so analytics
        # reflect completed interview history with actual answers.
        sessions = [s for s in all_sessions if s.responses]
        if not sessions:
            return InterviewCoachingAnalyticsResponse(
                session_count=0,
                answered_count_total=0,
                average_score_overall=None,
                score_delta_from_first_session=None,
                weakest_dimension_overall=None,
                recommended_focuses=[],
                recent_sessions=[],
            )

        session_coaching_items: list[InterviewCoachingRecentSession] = []
        first_session_avg: float | None = None
        latest_session_avg: float | None = None
        average_values: list[float] = []
        answered_count_total = 0
        dimension_totals: dict[str, int] = {}
        dimension_counts: dict[str, int] = {}

        chronological_sessions = sorted(
            sessions, key=lambda item: item.started_at or item.created_at
        )
        for session in chronological_sessions:
            sorted_responses = sorted(session.responses, key=lambda item: item.question_index)
            response_items = [self._build_feedback(response) for response in sorted_responses]
            trend_summary = InterviewTrendSummary(**build_trend_summary(response_items))
            answered_count = len(response_items)
            answered_count_total += answered_count
            session_average = trend_summary.average_score

            if session_average is not None:
                average_values.append(session_average)
                if first_session_avg is None:
                    first_session_avg = session_average
                latest_session_avg = session_average

            for response in response_items:
                for dimension in response.dimensions:
                    current_total = dimension_totals.get(dimension.dimension, 0)
                    current_count = dimension_counts.get(dimension.dimension, 0)
                    dimension_totals[dimension.dimension] = current_total + int(dimension.score)
                    dimension_counts[dimension.dimension] = current_count + 1

            session_coaching_items.append(
                InterviewCoachingRecentSession(
                    session_id=str(session.id),
                    practice_mode=session.practice_mode.value,
                    answered_count=answered_count,
                    average_score=session_average,
                    score_delta=trend_summary.score_delta,
                    score_direction=trend_summary.score_direction,
                    weakest_dimension_overall=trend_summary.weakest_dimension_overall,
                    completed_at=session.completed_at,
                    updated_at=session.updated_at,
                )
            )

        dimension_averages: dict[str, float] = {}
        for dimension, total in dimension_totals.items():
            count = dimension_counts.get(dimension, 0)
            if count <= 0:
                continue
            dimension_averages[dimension] = round(total / count, 2)

        weakest_dimension_overall = (
            min(
                dimension_averages.items(),
                key=lambda item: (item[1], item[0]),
            )[0]
            if dimension_averages
            else None
        )
        recommended_focuses = self._build_recommended_focuses(dimension_averages)

        score_delta_from_first_session = None
        if first_session_avg is not None and latest_session_avg is not None:
            score_delta_from_first_session = round(latest_session_avg - first_session_avg, 2)

        recent_sessions = sorted(
            session_coaching_items,
            key=lambda item: item.updated_at,
            reverse=True,
        )[:5]

        average_score_overall = (
            round(sum(average_values) / len(average_values), 2)
            if average_values
            else None
        )

        return InterviewCoachingAnalyticsResponse(
            session_count=len(sessions),
            answered_count_total=answered_count_total,
            average_score_overall=average_score_overall,
            score_delta_from_first_session=score_delta_from_first_session,
            weakest_dimension_overall=weakest_dimension_overall,
            recommended_focuses=recommended_focuses,
            recent_sessions=recent_sessions,
        )

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
                    audio_b64=payload.audio_b64 or "",
                    text_answer=payload.answer_text or "",
                )
            except Exception as exc:  # pragma: no cover
                print(f"Gemini evaluation failed, falling back to rules: {exc}")

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

        if session.current_question_index < session.total_questions:
            grounded_scholarships = await self._resolve_grounding(session.scholarship_id)
            weakest_dimension = select_weakest_dimension(feedback)
            base_next_question = session.question_set[session.current_question_index]
            session.question_set[session.current_question_index] = build_adaptive_question(
                base_next_question,
                weakest_dimension,
                grounded_scholarships,
            )

        if session.current_question_index >= session.total_questions:
            session.status = InterviewSessionStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc)
        else:
            session.status = InterviewSessionStatus.IN_PROGRESS

        await self.db.flush()
        await self.db.refresh(session)
        session = await self._load_session(user_id, session.id)
        response = self._build_session_response(session)
        await self._record_interview_kpi_snapshot(
            user_id=user_id,
            session_id=session.id,
            progression_metrics=response.progression_metrics,
            progression_gate=response.progression_gate,
        )
        return response

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

    async def _resolve_grounding(
        self,
        scholarship_id: str | uuid.UUID | None,
    ) -> list[Scholarship]:
        if scholarship_id is None:
            return []
        return await validate_scholarship_grounding(self.db, scholarship_id=scholarship_id)

    def _build_session_response(
        self,
        session: InterviewSession,
    ) -> InterviewSessionSummaryResponse:
        sorted_responses = sorted(session.responses, key=lambda item: item.question_index)
        response_items = [self._build_feedback(response) for response in sorted_responses]
        latest_feedback = response_items[-1] if response_items else None

        return InterviewSessionSummaryResponse(
            session_id=str(session.id),
            scholarship_id=str(session.scholarship_id) if session.scholarship_id else None,
            status=session.status.value,
            practice_mode=session.practice_mode.value,
            current_question_index=session.current_question_index,
            total_questions=session.total_questions,
            current_question=self._build_current_question(session),
            responses=response_items,
            latest_feedback=latest_feedback,
            history_summary=InterviewHistorySummary(**build_history_summary(response_items)),
            trend_summary=InterviewTrendSummary(**build_trend_summary(response_items)),
            progression_metrics=self._build_progression_metrics(response_items),
            progression_gate=self._build_progression_gate(response_items),
            started_at=session.started_at,
            completed_at=session.completed_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    async def _record_interview_kpi_snapshot(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        progression_metrics: InterviewProgressionMetrics,
        progression_gate: InterviewProgressionGate,
    ) -> None:
        await self.kpi_snapshot_service.record_interview_snapshot(
            user_id=user_id,
            session_id=session_id,
            policy_version=progression_gate.policy_version,
            kpi_passed=progression_gate.all_passed,
            metrics_payload=progression_metrics.model_dump(),
            gate_payload=progression_gate.model_dump(),
        )

    def _build_progression_gate(
        self,
        responses: list[InterviewAnswerFeedback],
    ) -> InterviewProgressionGate:
        thresholds = get_interview_progression_thresholds()
        metrics = self._build_progression_metrics(responses)

        answered_count_pass = metrics.answered_count >= thresholds.min_answered_count
        average_score_pass = (metrics.average_score or 0.0) >= thresholds.min_average_score
        score_delta_pass = (metrics.score_delta or 0.0) >= thresholds.min_score_delta
        needs_focus_ratio_pass = metrics.needs_focus_ratio <= thresholds.max_needs_focus_ratio

        return InterviewProgressionGate(
            thresholds=thresholds,
            policy_version=get_interview_progression_policy_version(),
            answered_count_pass=answered_count_pass,
            average_score_pass=average_score_pass,
            score_delta_pass=score_delta_pass,
            needs_focus_ratio_pass=needs_focus_ratio_pass,
            all_passed=(
                answered_count_pass
                and average_score_pass
                and score_delta_pass
                and needs_focus_ratio_pass
            ),
        )

    def _build_progression_metrics(
        self,
        responses: list[InterviewAnswerFeedback],
    ) -> InterviewProgressionMetrics:
        if not responses:
            return InterviewProgressionMetrics(
                answered_count=0,
                average_score=None,
                first_score=None,
                latest_score=None,
                score_delta=None,
                improvement_ratio=0.0,
                needs_focus_ratio=0.0,
            )

        scores = [response.overall_score for response in responses]
        first_score = scores[0]
        latest_score = scores[-1]
        score_delta = round(latest_score - first_score, 3)
        average_score = round(sum(scores) / len(scores), 3)
        improving_steps = 0
        for index in range(1, len(scores)):
            if scores[index] > scores[index - 1]:
                improving_steps += 1
        improvement_ratio = round(improving_steps / max(len(scores) - 1, 1), 4)

        needs_focus_count = sum(1 for score in scores if score < 3.0)
        needs_focus_ratio = round(needs_focus_count / len(scores), 4)

        return InterviewProgressionMetrics(
            answered_count=len(scores),
            average_score=average_score,
            first_score=first_score,
            latest_score=latest_score,
            score_delta=score_delta,
            improvement_ratio=improvement_ratio,
            needs_focus_ratio=needs_focus_ratio,
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
            allowed_modes = sorted(mode.value for mode in InterviewPracticeMode)
            allowed_text = "' or '".join(allowed_modes)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Interview practice mode must be '{allowed_text}'",
            ) from exc

    def _build_recommended_focuses(self, dimension_averages: dict[str, float]) -> list[str]:
        if not dimension_averages:
            return []

        focus_templates = {
            "clarity": "Lead with a three-part structure: context, evidence, and result.",
            "relevance": "Tie each answer directly to the prompt before adding supporting details.",
            "confidence": "Use direct ownership language about decisions, actions, and outcomes.",
            "specificity": "Add one concrete example with measurable impact in each answer.",
        }

        prioritized = sorted(
            dimension_averages.items(),
            key=lambda item: (item[1], item[0]),
        )
        focuses: list[str] = []
        for dimension, _score in prioritized[:2]:
            focuses.append(
                focus_templates.get(
                    dimension,
                    f"Strengthen {dimension} with specific evidence and concise structure.",
                )
            )
        return focuses
