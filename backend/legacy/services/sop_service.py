"""
SopService: Statement of Purpose generation and improvement using OpenAI GPT-4o.
"""
from __future__ import annotations

import logging
from typing import Optional, List

from app.core.config import settings
from app.models.models import StudentProfile, Scholarship

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are an expert academic writing consultant specialising in
scholarship applications. You write compelling, authentic Statements of Purpose
that highlight the applicant's unique strengths, align with the scholarship's
mission, and follow best practices in academic writing. Write in a clear,
confident, and personal voice. Avoid clichés. Be specific."""


class SopService:
    """Generate and improve Statements of Purpose using LLM completion."""

    def __init__(self):
        self._client = None  # lazy-init to avoid import cost at startup

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    # ── Generate ──────────────────────────────────────────────────────────────

    async def generate(
        self,
        profile: StudentProfile,
        scholarship: Scholarship,
        additional_context: str = "",
    ) -> dict:
        """Generate a full SOP draft tailored to a specific scholarship."""
        client = self._get_client()

        user_prompt = self._build_generation_prompt(profile, scholarship, additional_context)

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )

        text = response.choices[0].message.content.strip()
        suggestions = await self._generate_suggestions(text)

        return {
            "generated_text": text,
            "word_count":     len(text.split()),
            "suggestions":    suggestions,
        }

    # ── Improve ───────────────────────────────────────────────────────────────

    async def improve(
        self,
        current_sop: str,
        feedback_focus: Optional[str] = None,
    ) -> dict:
        """Improve an existing SOP based on optional focus area."""
        client = self._get_client()

        focus_instruction = ""
        if feedback_focus:
            focus_instruction = f"\nPrimary improvement focus: **{feedback_focus}**. Concentrate your rewrite on this area."

        user_prompt = f"""Please improve the following Statement of Purpose.{focus_instruction}

Return the improved version as plain text, followed by a brief list of key changes made.

--- ORIGINAL SOP ---
{current_sop}
"""

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=2000,
        )

        improved = response.choices[0].message.content.strip()
        return {
            "generated_text": improved,
            "word_count":     len(improved.split()),
            "suggestions":    None,
        }

    # ── Quick suggestions ─────────────────────────────────────────────────────

    async def _generate_suggestions(self, sop_text: str) -> List[str]:
        """Generate 3–5 actionable improvement tips for the generated SOP."""
        client = self._get_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a scholarly writing coach."},
                {
                    "role": "user",
                    "content": (
                        f"List 3-5 concise, actionable suggestions to improve this SOP "
                        f"(as a JSON array of strings):\n\n{sop_text[:800]}"
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        import json
        raw = response.choices[0].message.content
        data = json.loads(raw)
        return data.get("suggestions", data.get("items", []))

    # ── Prompt builder ────────────────────────────────────────────────────────

    @staticmethod
    def _build_generation_prompt(
        profile: StudentProfile,
        scholarship: Scholarship,
        additional_context: str,
    ) -> str:
        bullet = lambda k, v: f"• {k}: {v}" if v else ""

        student_info = "\n".join(filter(None, [
            bullet("Field of study",   profile.field_of_study),
            bullet("Degree level",     profile.degree_level),
            bullet("University",       profile.university),
            bullet("GPA",              f"{profile.gpa}/{profile.gpa_scale}" if profile.gpa else None),
            bullet("Research publications", profile.research_publications or None),
            bullet("Research experience",  f"{profile.research_experience_months} months" if profile.research_experience_months else None),
            bullet("Leadership roles", profile.leadership_roles or None),
            bullet("Volunteer hours",  profile.volunteer_hours or None),
            bullet("Language test",    f"{profile.language_test_type} {profile.language_test_score}" if profile.language_test_type else None),
            bullet("Extracurriculars", profile.extracurricular_summary),
            bullet("Draft notes",      profile.sop_draft[:400] if profile.sop_draft else None),
        ]))

        scholarship_info = "\n".join(filter(None, [
            bullet("Scholarship name",   scholarship.name),
            bullet("Provider",           scholarship.provider),
            bullet("Country",            scholarship.country),
            bullet("University",         scholarship.university),
            bullet("Fields supported",   ", ".join(scholarship.field_of_study or [])),
            bullet("Degree levels",      ", ".join(scholarship.degree_levels or [])),
            bullet("Funding type",       scholarship.funding_type),
            bullet("Description",        (scholarship.description or "")[:500]),
        ]))

        extra = f"\nAdditional context from applicant:\n{additional_context}" if additional_context else ""

        return f"""Write a compelling Statement of Purpose (600-900 words) for the following applicant and scholarship.

## Applicant Profile
{student_info}

## Target Scholarship
{scholarship_info}
{extra}

Guidelines:
- Open with a compelling hook that reflects the applicant's genuine motivation
- Demonstrate fit between the applicant's background and the scholarship's mission
- Use specific examples and achievements (not generic statements)
- Include a clear research/career vision
- Close with a forward-looking statement about impact
- Write in first person, active voice
- Do NOT include headers or bullet points — flowing prose only
"""
