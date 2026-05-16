"""Visa interview simulator service (Feature 8, PRD §8).

Owns:
- Session creation against the 70-question Pakistani-context bank.
- Answer evaluation pipeline (Claude → deterministic fallback).
- Free-tier Q3 cutoff (HTTP 402 with partial summary).
- Elite-only downloadable transcript persisted as a DocumentRecord.
- Session summary with rubric breakdown.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_guard import (
    get_price_for_currency,
    has_plan_at_least,
    raise_plan_required,
)
from app.models import (
    DocumentInputMethod,
    DocumentProcessingStatus,
    DocumentRecord,
    DocumentType,
    InterviewPracticeMode,
    InterviewResponse,
    InterviewSession,
    InterviewSessionStatus,
    User,
    VisaInterviewQuestion,
)
from app.schemas.visa_interview import (
    VisaInterviewAnswerRequest,
    VisaInterviewAnswerResponse,
    VisaInterviewProgress,
    VisaInterviewQuestionDTO,
    VisaInterviewRubric,
    VisaInterviewSessionSummary,
    VisaInterviewStartRequest,
    VisaInterviewStartResponse,
)
from app.services.visa_interview.evaluator import evaluate_answer


logger = logging.getLogger(__name__)


FREE_PLAN_ANSWER_LIMIT = 3
SESSION_QUESTION_COUNT = 10
VISA_TYPE_BY_COUNTRY = {
    "GB": "student_uk",
    "US": "f1_us",
    "CA": "study_ca",
    "DE": "student_de",
}


class VisaInterviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def start(
        self,
        user: User,
        payload: VisaInterviewStartRequest,
    ) -> VisaInterviewStartResponse:
        visa_type = payload.visa_type or VISA_TYPE_BY_COUNTRY.get(payload.country)
        if not visa_type:
            raise ValueError(f"No visa_type mapping for country {payload.country}")

        bank = await self._fetch_question_bank(payload.country, visa_type)
        if not bank:
            raise ValueError(
                "Visa question bank is empty for this country. "
                "Run scripts/seed_visa_interview_questions.py first."
            )

        question_ids = [str(q.id) for q in bank[:SESSION_QUESTION_COUNT]]
        session = InterviewSession(
            user_id=user.id,
            practice_mode=InterviewPracticeMode(payload.practice_mode)
            if payload.practice_mode in {m.value for m in InterviewPracticeMode}
            else InterviewPracticeMode.GENERAL,
            status=InterviewSessionStatus.IN_PROGRESS,
            scholarship_id=payload.scholarship_id,
            country=payload.country,
            visa_type=visa_type,
            current_question_index=0,
            total_questions=len(question_ids),
            question_set=question_ids,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        first = bank[0] if bank else None
        return VisaInterviewStartResponse(
            session_id=session.id,
            country=session.country,
            visa_type=session.visa_type,
            practice_mode=session.practice_mode.value,
            total_questions=session.total_questions,
            first_question=_to_question_dto(first) if first else None,
            started_at=session.started_at,
        )

    async def answer(
        self,
        user: User,
        session_id: uuid.UUID,
        payload: VisaInterviewAnswerRequest,
    ) -> VisaInterviewAnswerResponse:
        session = await self._get_owned_session(user.id, session_id)
        if session is None:
            raise LookupError("Interview session not found")

        question = await self.db.get(VisaInterviewQuestion, payload.question_id)
        if question is None:
            raise LookupError("Question not found")

        answered_so_far = await self._count_answers(session.id)

        # Free-tier cutoff after the 3rd answer.
        if not has_plan_at_least(user, "pro", "elite", "institution"):
            if answered_so_far >= FREE_PLAN_ANSWER_LIMIT:
                partial = await self._partial_summary(session.id)
                price = get_price_for_currency(user.plan_currency)
                raise_plan_required(
                    user,
                    ["pro", "elite", "institution"],
                    message=(
                        f"You got {partial['red_flag_count']} red flags in your first "
                        f"{FREE_PLAN_ANSWER_LIMIT} answers. Questions 4–10 expose the weakest "
                        f"parts. Finish for {price}."
                    ),
                    extra={
                        "error": "plan_limit_reached",
                        "partial_summary": partial,
                    },
                )

        rubric_data = await evaluate_answer(
            db=self.db,
            user=user,
            country=session.country or "GB",
            question_text=question.question_text,
            category=question.category,
            answer_text=payload.answer_text,
        )

        response = InterviewResponse(
            session_id=session.id,
            question_index=answered_so_far,
            question_text=question.question_text,
            answer_text=payload.answer_text,
            score_payload=rubric_data,
            summary_feedback=rubric_data.get("what_was_good", ""),
        )
        self.db.add(response)

        session.current_question_index = answered_so_far + 1
        next_question_dto = None
        if session.current_question_index < session.total_questions:
            qid = uuid.UUID(session.question_set[session.current_question_index])
            next_q = await self.db.get(VisaInterviewQuestion, qid)
            if next_q:
                next_question_dto = _to_question_dto(next_q)
        else:
            session.status = InterviewSessionStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(session)

        progress = VisaInterviewProgress(
            answered=session.current_question_index,
            total=session.total_questions,
        )

        # Elite transcript generated when the session closes.
        if (
            session.status == InterviewSessionStatus.COMPLETED
            and has_plan_at_least(user, "elite", "institution")
        ):
            await self._generate_transcript(user, session)

        return VisaInterviewAnswerResponse(
            evaluation=VisaInterviewRubric(**rubric_data),
            next_question=next_question_dto,
            session_progress=progress,
        )

    async def summary(
        self,
        user: User,
        session_id: uuid.UUID,
    ) -> VisaInterviewSessionSummary:
        session = await self._get_owned_session(user.id, session_id)
        if session is None:
            raise LookupError("Interview session not found")

        result = await self.db.execute(
            select(InterviewResponse)
            .where(InterviewResponse.session_id == session.id)
            .order_by(InterviewResponse.question_index.asc())
        )
        responses = list(result.scalars().all())

        breakdown, red_flag_count, areas = _aggregate(responses)
        avg = round(
            (
                breakdown.get("clarity", 0.0)
                + breakdown.get("confidence", 0.0)
                + breakdown.get("relevance", 0.0)
            )
            / 3,
            2,
        ) if breakdown else 0.0

        transcript_doc_id = await self._latest_transcript_id(user.id, session.id)

        return VisaInterviewSessionSummary(
            session_id=session.id,
            country=session.country or "",
            visa_type=session.visa_type or "",
            answered=len(responses),
            total=session.total_questions,
            average_score=avg,
            score_breakdown=breakdown,
            red_flag_count=red_flag_count,
            areas_to_improve=areas,
            transcript_document_id=transcript_doc_id,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _fetch_question_bank(self, country: str, visa_type: str) -> list[VisaInterviewQuestion]:
        result = await self.db.execute(
            select(VisaInterviewQuestion)
            .where(
                VisaInterviewQuestion.country == country,
                VisaInterviewQuestion.visa_type == visa_type,
                VisaInterviewQuestion.is_active.is_(True),
            )
            .order_by(VisaInterviewQuestion.created_at.asc())
            .limit(SESSION_QUESTION_COUNT)
        )
        return list(result.scalars().all())

    async def _get_owned_session(
        self, user_id: uuid.UUID, session_id: uuid.UUID
    ) -> InterviewSession | None:
        result = await self.db.execute(
            select(InterviewSession).where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _count_answers(self, session_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(InterviewResponse)
            .where(InterviewResponse.session_id == session_id)
        )
        return int(result.scalar() or 0)

    async def _partial_summary(self, session_id: uuid.UUID) -> dict[str, Any]:
        result = await self.db.execute(
            select(InterviewResponse).where(InterviewResponse.session_id == session_id)
        )
        rows = list(result.scalars().all())
        breakdown, red_flag_count, _ = _aggregate(rows)
        return {
            "answered": len(rows),
            "red_flag_count": red_flag_count,
            "score_breakdown": breakdown,
        }

    async def _generate_transcript(self, user: User, session: InterviewSession) -> None:
        result = await self.db.execute(
            select(InterviewResponse)
            .where(InterviewResponse.session_id == session.id)
            .order_by(InterviewResponse.question_index.asc())
        )
        rows = list(result.scalars().all())
        lines = [
            f"# Visa Interview Transcript — {session.country} / {session.visa_type}",
            f"Date: {datetime.now(timezone.utc).date().isoformat()}",
            "",
        ]
        for idx, row in enumerate(rows, start=1):
            payload = row.score_payload or {}
            lines.append(f"## Question {idx}")
            lines.append(f"**Q:** {row.question_text}")
            lines.append(f"**A:** {row.answer_text}")
            lines.append(
                f"**Score:** clarity {payload.get('clarity_score', '?')}, "
                f"confidence {payload.get('confidence_score', '?')}, "
                f"relevance {payload.get('relevance_score', '?')} — "
                f"overall {payload.get('overall_score', '?')}"
            )
            if payload.get("red_flags"):
                lines.append("**Red flags:** " + "; ".join(payload["red_flags"]))
            if payload.get("missing_elements"):
                lines.append("**Missing:** " + "; ".join(payload["missing_elements"]))
            lines.append(f"**What worked:** {payload.get('what_was_good', '')}")
            lines.append(f"**Ideal answer summary:** {payload.get('ideal_answer_summary', '')}")
            lines.append("")
        transcript = "\n".join(lines)

        document = DocumentRecord(
            user_id=user.id,
            title=f"Visa Interview Transcript — {session.country}",
            document_type=DocumentType.SOP,  # reuse existing enum slot for transcript persistence
            input_method=DocumentInputMethod.TEXT,
            content_text=transcript,
            processing_status=DocumentProcessingStatus.COMPLETED,
        )
        # Mark as interview transcript via the persistent provenance hint on title.
        # The DocumentType enum stays as-is so we don't churn migrations; the title
        # prefix lets the API surface render the right artefact.
        self.db.add(document)
        await self.db.flush()

    async def _latest_transcript_id(
        self, user_id: uuid.UUID, session_id: uuid.UUID
    ) -> uuid.UUID | None:
        result = await self.db.execute(
            select(DocumentRecord.id)
            .where(
                DocumentRecord.user_id == user_id,
                DocumentRecord.title.like("Visa Interview Transcript%"),
            )
            .order_by(DocumentRecord.created_at.desc())
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None


def _to_question_dto(q: VisaInterviewQuestion) -> VisaInterviewQuestionDTO:
    return VisaInterviewQuestionDTO(
        id=q.id,
        country=q.country,
        visa_type=q.visa_type,
        category=q.category,
        question_text=q.question_text,
        difficulty=q.difficulty,
    )


def _aggregate(responses: list[InterviewResponse]) -> tuple[dict[str, float], int, list[str]]:
    if not responses:
        return {}, 0, []
    clarity = 0.0
    confidence = 0.0
    relevance = 0.0
    overall = 0.0
    red_flag_count = 0
    missing_corpus: list[str] = []
    for row in responses:
        payload = row.score_payload or {}
        clarity += float(payload.get("clarity_score", 0) or 0)
        confidence += float(payload.get("confidence_score", 0) or 0)
        relevance += float(payload.get("relevance_score", 0) or 0)
        overall += float(payload.get("overall_score", 0) or 0)
        red_flag_count += len(payload.get("red_flags") or [])
        missing_corpus.extend(payload.get("missing_elements") or [])
    n = len(responses)
    breakdown = {
        "clarity": round(clarity / n, 2),
        "confidence": round(confidence / n, 2),
        "relevance": round(relevance / n, 2),
        "overall": round(overall / n, 2),
    }
    # Top 3 most-frequent missing-element bullets become areas to improve.
    counts: dict[str, int] = {}
    for line in missing_corpus:
        counts[line] = counts.get(line, 0) + 1
    areas = [line for line, _ in sorted(counts.items(), key=lambda kv: -kv[1])][:3]
    return breakdown, red_flag_count, areas
