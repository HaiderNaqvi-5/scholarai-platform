"""Pakistan-context SOP generation (Feature 7, PRD §7).

Owns the prompt + the deterministic fallback. Persists the generated draft
as a DocumentRecord so the rest of the document pipeline (feedback, history,
deletion) keeps working unchanged.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.plan_guard import (
    assert_plan_or_raise,
    get_price_for_currency,
    has_plan_at_least,
    raise_plan_required,
)
from app.models import (
    DocumentInputMethod,
    DocumentProcessingStatus,
    DocumentRecord,
    DocumentType,
    Scholarship,
    User,
)
from app.schemas.sop import (
    SOPDraftRequest,
    SOPDraftResponse,
    SOPGroundedContext,
    SOPInputs,
    SOPParagraphFeedback,
)
from app.services.llm import AnthropicClient, LLMUnavailableError


logger = logging.getLogger(__name__)


PARAGRAPH_LABELS = ["Opening", "Background", "Experience", "Motivation", "Goals", "Closing"]


SOP_SYSTEM_PROMPT = """You are an expert SOP writer specializing in Pakistani
students applying to graduate programs abroad. You understand:
- Pakistani academic context (HEC, NUST, LUMS, FAST, UET, COMSATS, IBA).
- Common weaknesses in Pakistani SOPs: generic motivation, lack of research
  narrative, no connection between past and future.
- That Pakistani students often have limited research publications but
  strong coursework and industry experience.
- The importance of showing commitment to contributing back (for
  government scholarships) or global ambition (for university scholarships).
- Visa officer concerns: ties to Pakistan, intent to return, genuine
  student intent.

Generate a 600-800 word SOP draft. Structure: hook opening -> academic
background -> research/professional experience -> why this specific
program / university -> career goals -> closing. Use the student's inputs.
Be specific, not generic. Avoid clichés. If scholarship_context is
provided, align the SOP narrative to that scholarship's values.

Return the SOP as plain prose with six paragraphs separated by blank
lines. Do NOT prefix paragraphs with labels — labels are added by the
client. Do NOT include any preamble before or after the SOP."""


LINE_FEEDBACK_SYSTEM_PROMPT = """You are a senior admissions reviewer.
For each paragraph of an SOP, identify: what works well (one sentence),
what is weak or generic (be specific), and a suggested rewrite for the
weakest sentence.

Return strict JSON:
{
  "paragraphs": [
    {
      "index": 1,
      "strength": "...",
      "weakness": "...",
      "suggestion": "..."
    }
  ]
}

Do not include any prose outside of the JSON object."""


class SOPBuilderService:
    def __init__(self, db: AsyncSession, llm: AnthropicClient | None = None) -> None:
        self.db = db
        self.llm = llm or AnthropicClient()

    async def draft(self, user: User, payload: SOPDraftRequest) -> SOPDraftResponse:
        await self._enforce_free_tier_limit(user)

        scholarship_context = await self._scholarship_context(payload.scholarship_id)
        draft_text, used_llm, model_used = self._generate_draft(payload, scholarship_context)
        paragraphs = _split_paragraphs(draft_text)

        document = DocumentRecord(
            user_id=user.id,
            title=payload.program_name or "Statement of Purpose",
            document_type=DocumentType.SOP,
            input_method=DocumentInputMethod.TEXT,
            content_text=draft_text,
            processing_status=DocumentProcessingStatus.COMPLETED,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        grounded_context = SOPGroundedContext(
            validated_scholarship_facts=scholarship_context.get("facts", []) if scholarship_context else [],
            retrieved_writing_guidance=[
                "Pakistani SOPs read strongest when they translate measurable academic"
                " outcomes (CGPA, projects, ranking) into concrete future contributions.",
                "Avoid clichéd phrases like 'since childhood' and 'world-class'.",
                "Cite at least one specific course, professor, or lab to anchor program fit.",
            ],
            generated_guidance=(
                "This draft was generated against your inputs. Personalise it before submission;"
                " admissions committees can detect generic AI writing."
            ),
            limitations=(
                "This SOP draft is AI-generated and may contain factual errors. Verify all"
                " claims, dates, and citations before submission. AI-generated content is not"
                " a substitute for licensed advisor review."
            ),
        )

        line_feedback: list[SOPParagraphFeedback] | None = None
        if has_plan_at_least(user, "elite", "institution"):
            line_feedback = self._generate_line_feedback(draft_text, paragraphs)

        return SOPDraftResponse(
            document_id=document.id,
            draft_content=draft_text,
            word_count=_word_count(draft_text),
            paragraph_labels=PARAGRAPH_LABELS[: len(paragraphs)] or PARAGRAPH_LABELS,
            grounded_context=grounded_context,
            line_feedback=line_feedback,
            model_used=model_used,
            used_llm=used_llm,
            created_at=document.created_at or datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _enforce_free_tier_limit(self, user: User) -> None:
        if has_plan_at_least(user, "pro", "elite", "institution"):
            return
        result = await self.db.execute(
            select(func.count())
            .select_from(DocumentRecord)
            .where(
                DocumentRecord.user_id == user.id,
                DocumentRecord.document_type == DocumentType.SOP,
            )
        )
        existing = int(result.scalar() or 0)
        if existing >= 1:
            price = get_price_for_currency(user.plan_currency)
            raise_plan_required(
                user,
                ["pro", "elite", "institution"],
                message=(
                    f"Want to adapt this SOP for another university? Pro users generate"
                    f" unlimited SOPs ({price}, less than one consultant draft)."
                ),
                extra={"error": "plan_limit_reached", "existing_sops": existing},
            )

    async def _scholarship_context(self, scholarship_id: uuid.UUID | None) -> dict[str, Any] | None:
        if scholarship_id is None:
            return None
        row = await self.db.get(Scholarship, scholarship_id)
        if row is None:
            return None
        facts: list[str] = []
        if row.title:
            facts.append(f"Target scholarship: {row.title}.")
        if row.provider_name:
            facts.append(f"Provider: {row.provider_name}.")
        if row.country_code:
            facts.append(f"Hosting country: {row.country_code}.")
        if row.funding_summary:
            facts.append(f"Funding scope: {row.funding_summary}")
        if row.deadline_at:
            facts.append(f"Application deadline: {row.deadline_at.date().isoformat()}.")
        return {"facts": facts, "summary": row.summary, "tags": list(row.field_tags or [])}

    def _generate_draft(
        self,
        payload: SOPDraftRequest,
        scholarship_context: dict[str, Any] | None,
    ) -> tuple[str, bool, str]:
        user_prompt = _build_user_prompt(payload, scholarship_context)
        if self.llm.available:
            try:
                text = self.llm.call_text(
                    system_prompt=SOP_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    model=settings.ANTHROPIC_MODEL_DEEP,
                    max_tokens=1800,
                    temperature=0.4,
                )
                if text and _word_count(text) >= 300:
                    return text, True, settings.ANTHROPIC_MODEL_DEEP
                logger.warning("Claude SOP draft too short; falling back to template.")
            except LLMUnavailableError:
                pass
            except Exception:  # pragma: no cover - network failures
                logger.exception("Claude SOP draft failed; falling back to deterministic template.")
        return _deterministic_draft(payload, scholarship_context), False, "deterministic_template"

    def _generate_line_feedback(
        self,
        draft_text: str,
        paragraphs: list[str],
    ) -> list[SOPParagraphFeedback]:
        if not self.llm.available:
            return _deterministic_line_feedback(paragraphs)
        try:
            data = self.llm.call_json(
                system_prompt=LINE_FEEDBACK_SYSTEM_PROMPT,
                user_prompt=f"SOP draft:\n\n{draft_text}",
                model=settings.ANTHROPIC_MODEL_DEEP,
                max_tokens=1500,
                temperature=0.2,
            )
        except (LLMUnavailableError, Exception):  # pragma: no cover - network failures
            return _deterministic_line_feedback(paragraphs)
        rows = data.get("paragraphs") or []
        feedback: list[SOPParagraphFeedback] = []
        for idx, raw in enumerate(rows[: len(paragraphs)], start=1):
            feedback.append(
                SOPParagraphFeedback(
                    index=raw.get("index", idx),
                    paragraph_label=PARAGRAPH_LABELS[idx - 1] if idx - 1 < len(PARAGRAPH_LABELS) else f"Section {idx}",
                    strength=str(raw.get("strength", "")).strip()
                    or "Establishes the section's intent.",
                    weakness=str(raw.get("weakness", "")).strip()
                    or "Could be more specific.",
                    suggestion=str(raw.get("suggestion", "")).strip()
                    or "Anchor the claim with one concrete detail (course, project, or metric).",
                )
            )
        return feedback or _deterministic_line_feedback(paragraphs)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _word_count(text: str) -> int:
    return len([w for w in (text or "").split() if w.strip()])


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in (text or "").split("\n\n") if p.strip()]


def _build_user_prompt(payload: SOPDraftRequest, ctx: dict[str, Any] | None) -> str:
    inputs = payload.sop_inputs
    block = []
    if payload.program_name:
        block.append(f"Target program: {payload.program_name}")
    if ctx:
        block.append("Scholarship context: " + " ".join(ctx.get("facts", [])))
        if ctx.get("summary"):
            block.append(f"Scholarship summary: {ctx['summary']}")
    block.append(f"Academic background: {inputs.academic_background}")
    if inputs.research_experience:
        block.append(f"Research experience: {inputs.research_experience}")
    if inputs.professional_experience:
        block.append(f"Professional experience: {inputs.professional_experience}")
    block.append(f"Why this program: {inputs.why_this_program}")
    if inputs.why_this_country:
        block.append(f"Why this country: {inputs.why_this_country}")
    block.append(f"Career goals: {inputs.career_goals}")
    if inputs.challenges_overcome:
        block.append(f"Challenges overcome: {inputs.challenges_overcome}")
    if inputs.gap_explanation:
        block.append(f"Gap explanation: {inputs.gap_explanation}")
    return "\n\n".join(block)


def _deterministic_draft(payload: SOPDraftRequest, ctx: dict[str, Any] | None) -> str:
    inputs = payload.sop_inputs
    program = payload.program_name or "this program"
    country_clause = inputs.why_this_country or (
        "an environment with deep research infrastructure and Pakistani alumni networks"
    )
    challenge_para = inputs.challenges_overcome or (
        "Coming from a context where postgraduate research culture is still emerging, I "
        "have learned to build my own opportunities — reading papers off-syllabus, "
        "cold-emailing faculty, and turning side projects into peer-reviewed submissions."
    )
    research_clause = inputs.research_experience or (
        "Beyond coursework I led applied projects with industry mentors that translated "
        "academic concepts into working systems."
    )
    pro_clause = inputs.professional_experience or (
        "I balanced rigorous study with internships and freelance engineering work, which "
        "sharpened my judgment about which technical problems are worth pursuing at scale."
    )
    gap_clause = (
        f"\n\nGap context: {inputs.gap_explanation}" if inputs.gap_explanation else ""
    )

    facts_tail = (
        " This application is anchored to the following validated scholarship "
        "context: " + " ".join(ctx["facts"])
        if ctx and ctx.get("facts")
        else ""
    )
    gap_inline = f" {inputs.gap_explanation}" if inputs.gap_explanation else ""

    paragraphs = [
        # Opening
        (
            f"Pakistan ranks among the world's most populous countries yet remains "
            f"under-represented in the global research conversation in my field. "
            f"My ambition is to close that gap. I am applying to {program} because it "
            f"offers the exact combination of rigorous training and applied research "
            f"that the next chapter of my career requires."
            f"{facts_tail}"
        ),
        # Background
        f"Academic foundation. {inputs.academic_background}",
        # Experience (single paragraph — research + professional joined by sentence)
        f"{research_clause} {pro_clause}",
        # Motivation
        (
            f"Why {program} specifically. {inputs.why_this_program} "
            f"I am drawn to {country_clause}, which gives me access to the labs, peer "
            f"networks, and industry partnerships that my Pakistani undergraduate "
            f"training prepared me for but could not by itself provide."
        ),
        # Goals
        (
            f"My career goals. {inputs.career_goals} "
            "I intend to translate the training into measurable contribution — "
            "publishing where appropriate, mentoring Pakistani undergraduates, and "
            "channelling expertise back into Pakistan's higher-education ecosystem."
        ),
        # Closing
        (
            f"{challenge_para}{gap_inline} I believe my profile is a credible match "
            f"for {program}, and I am committed to making the most of the opportunity. "
            "Thank you for considering my application."
        ),
    ]
    return "\n\n".join(paragraphs)


def _deterministic_line_feedback(paragraphs: list[str]) -> list[SOPParagraphFeedback]:
    out: list[SOPParagraphFeedback] = []
    for idx, paragraph in enumerate(paragraphs[: len(PARAGRAPH_LABELS)], start=1):
        label = PARAGRAPH_LABELS[idx - 1]
        out.append(
            SOPParagraphFeedback(
                index=idx,
                paragraph_label=label,
                strength=f"{label} paragraph establishes the narrative anchor.",
                weakness=(
                    "Statements are still abstract — admissions readers reward specific "
                    "courses, mentors, or measurable outcomes."
                ),
                suggestion=(
                    "Replace the weakest sentence with one verifiable detail — a specific "
                    "course, a project metric, a named professor, or a quantified result."
                ),
            )
        )
    return out
