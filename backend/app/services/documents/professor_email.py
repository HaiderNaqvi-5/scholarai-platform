"""Elite professor cold-email generator (PRD §0.6).

Generates a personalised PhD/RA outreach email for Pakistani students. Gated
to elite + institution plans. Persists the result as a DocumentRecord so it
shows up in GET /documents alongside SOPs. Mirrors the SOPBuilderService
shape: Claude with a deterministic-template fallback so CI stays green offline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.plan_guard import assert_plan_or_raise
from app.models import (
    DocumentInputMethod,
    DocumentProcessingStatus,
    DocumentRecord,
    DocumentType,
    User,
)
from app.schemas.professor_email import ProfessorEmailRequest, ProfessorEmailResponse
from app.services.llm import AnthropicClient, LLMUnavailableError


logger = logging.getLogger(__name__)


PROFESSOR_EMAIL_SYSTEM_PROMPT = """You write concise, credible cold emails for
Pakistani students reaching out to professors abroad for PhD or RA positions.
You understand:
- Pakistani students often have strong coursework and industry projects but
  few publications — lead with concrete, verifiable work, not adjectives.
- Professors skim. The email must be under 200 words, specific in the first
  two sentences, and end with a clear, low-friction ask.
- Reference the professor's actual research area so it does not read as a
  mass email. Never invent papers, grants, or results.

Return strict JSON:
{"subject": "...", "body": "..."}
The body is plain text with greeting, 2-3 short paragraphs, and a sign-off
placeholder line "[Your name]". No preamble outside the JSON object."""


LIMITATIONS_NOTE = (
    "This email is AI-generated from your inputs. Verify the professor's name,"
    " research area, and current openings before sending. Personalise it —"
    " professors can detect generic outreach."
)


class ProfessorEmailService:
    def __init__(self, db: AsyncSession, llm: AnthropicClient | None = None) -> None:
        self.db = db
        self.llm = llm or AnthropicClient()

    async def generate(
        self, user: User, payload: ProfessorEmailRequest
    ) -> ProfessorEmailResponse:
        # Elite-exclusive (PRD §0.6). institution rank also passes.
        assert_plan_or_raise(
            user,
            "elite",
            "institution",
            message=(
                "The professor cold-email generator is an Elite feature. "
                "Upgrade to generate personalised PhD/RA outreach emails."
            ),
        )

        subject, body, used_llm, model_used = await self._generate(user, payload)
        word_count = len([w for w in body.split() if w.strip()])

        document = DocumentRecord(
            user_id=user.id,
            title=f"Email to {payload.professor_name} — {payload.university}",
            document_type=DocumentType.PROFESSOR_EMAIL,
            input_method=DocumentInputMethod.TEXT,
            content_text=f"Subject: {subject}\n\n{body}",
            processing_status=DocumentProcessingStatus.COMPLETED,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        return ProfessorEmailResponse(
            document_id=document.id,
            email_subject=subject,
            email_body=body,
            word_count=word_count,
            used_llm=used_llm,
            model_used=model_used,
            limitations=LIMITATIONS_NOTE,
            created_at=document.created_at or datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------

    async def _generate(
        self, user: User, payload: ProfessorEmailRequest
    ) -> tuple[str, str, bool, str]:
        user_prompt = (
            f"Professor: {payload.professor_name}\n"
            f"University: {payload.university}\n"
            f"Research area: {payload.research_area}\n"
            f"Position sought: {payload.position_type}\n"
            f"Student background and fit: {payload.student_pitch}"
        )
        try:
            data = await self.llm.complete_with_accounting(
                db=self.db,
                user=user,
                endpoint="documents.professor_email",
                system_prompt=PROFESSOR_EMAIL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=settings.ANTHROPIC_MODEL_DEEP,
                max_tokens=900,
                temperature=0.5,
                json_mode=True,
            )
            if isinstance(data, dict):
                subject = str(data.get("subject", "")).strip()
                body = str(data.get("body", "")).strip()
                if subject and len(body.split()) >= 40:
                    return subject, body, True, settings.ANTHROPIC_MODEL_DEEP
                logger.warning("Claude professor-email output too thin; using template.")
        except LLMUnavailableError:
            pass
        except HTTPException:
            # Burn-cap exhaustion (429) — propagate to caller.
            raise
        except Exception:  # pragma: no cover - network failures
            logger.exception("Claude professor-email failed; using deterministic template.")
        subject, body = _deterministic_email(payload)
        return subject, body, False, "deterministic_template"


def _deterministic_email(payload: ProfessorEmailRequest) -> tuple[str, str]:
    ask = (
        "a fully-funded PhD position in your group"
        if payload.position_type.lower() == "phd"
        else "a research assistantship in your lab"
    )
    subject = (
        f"Prospective {payload.position_type.upper()} applicant — "
        f"{payload.research_area}"
    )
    body = (
        f"Dear Professor {payload.professor_name},\n\n"
        f"I am writing to ask about {ask} at {payload.university}. Your work on "
        f"{payload.research_area} maps closely onto what I have built and want to "
        f"pursue next.\n\n"
        f"{payload.student_pitch.strip()}\n\n"
        f"I would value the chance to discuss whether my background fits your "
        f"current projects. I can share my CV, transcripts, and a short research "
        f"statement on request. Thank you for your time and consideration.\n\n"
        f"Best regards,\n[Your name]"
    )
    return subject, body
