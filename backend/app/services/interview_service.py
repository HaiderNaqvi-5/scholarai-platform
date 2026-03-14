"""
InterviewService: AI-powered mock interview coach using OpenAI GPT-4o.

Supports:
  - Generating contextual questions (scholarship + profile-aware)
  - Evaluating student answers with detailed feedback
  - Full session management (tracks question/answer pairs)
"""
from __future__ import annotations

import logging
import json
from typing import List, Optional

from app.core.config import settings
from app.models.models import StudentProfile, Scholarship

logger = logging.getLogger(__name__)


INTERVIEWER_SYSTEM = """You are an expert scholarship interview coach who has helped
thousands of students win prestigious scholarships. You ask probing, insightful
questions and give honest, actionable feedback. Your tone is warm yet rigorous.
Be specific and constructive."""


class InterviewService:
    """Generate mock interview questions and evaluate answers."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    # ── Generate questions ─────────────────────────────────────────────────────

    async def generate_questions(
        self,
        profile: StudentProfile,
        scholarship: Scholarship,
        question_count: int = 5,
        focus_areas: Optional[List[str]] = None,
    ) -> List[dict]:
        """Return a list of interview questions tailored to student + scholarship."""
        client = self._get_client()

        focus_str = ""
        if focus_areas:
            focus_str = f"\nFocus specifically on these areas: {', '.join(focus_areas)}."

        prompt = f"""Generate {question_count} interview questions for a scholarship candidate.
{focus_str}

Scholarship: {scholarship.name} ({scholarship.provider})
Country: {scholarship.country}
Fields: {', '.join(scholarship.field_of_study or [])}

Student profile:
• Field: {profile.field_of_study}
• Degree level: {profile.degree_level}
• GPA: {profile.gpa}/{profile.gpa_scale if profile.gpa else 'not provided'}
• Research publications: {profile.research_publications or 0}
• Leadership roles: {profile.leadership_roles or 0}

Return a JSON object with key "questions", each item having:
- "question": the interview question (string)
- "category": one of [motivation, research, leadership, cultural_fit, career_vision, personal]
- "difficulty": one of [easy, medium, hard]
- "tip": a brief coaching tip for answering this question
"""

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": INTERVIEWER_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.8,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("questions", [])

    # ── Evaluate answer ────────────────────────────────────────────────────────

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        profile: StudentProfile,
        scholarship: Optional[Scholarship] = None,
    ) -> dict:
        """Score and provide detailed feedback on a student's interview answer."""
        client = self._get_client()

        sch_context = ""
        if scholarship:
            sch_context = f"\nScholarship: {scholarship.name} ({scholarship.provider}, {scholarship.country})"

        prompt = f"""Evaluate this interview answer for a scholarship applicant.
{sch_context}

QUESTION: {question}

STUDENT'S ANSWER: {answer}

Return a JSON object with:
- "score": integer 1-10
- "overall_feedback": 2-3 sentence assessment
- "strengths": list of 2-3 string strengths
- "improvements": list of 2-3 specific, actionable improvement suggestions
- "sample_strong_answer": a brief example of how to strengthen one key aspect
- "star_usage": boolean — did they use Situation/Task/Action/Result structure?
"""

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": INTERVIEWER_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

    # ── Full session evaluation ────────────────────────────────────────────────

    async def evaluate_session(self, session_qa_pairs: List[dict]) -> dict:
        """Aggregate feedback across a full mock interview session (list of Q+A pairs)."""
        client = self._get_client()

        qa_text = "\n\n".join([
            f"Q{i+1}: {pair['question']}\nA{i+1}: {pair['answer']}"
            for i, pair in enumerate(session_qa_pairs)
        ])

        prompt = f"""Review this complete mock interview session and provide a holistic evaluation.

{qa_text}

Return JSON with:
- "overall_score": float 1-10
- "readiness_level": one of [not_ready, developing, ready, highly_ready]
- "top_strengths": list of strings
- "critical_improvements": list of strings
- "recommendation": 2-3 sentence recommendation for next steps
"""

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": INTERVIEWER_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.2,
            max_tokens=700,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
