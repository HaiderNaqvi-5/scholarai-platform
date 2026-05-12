"""Visa-officer-style evaluation logic (Feature 8, PRD §8).

The Claude path uses a single JSON-mode call; the deterministic path scores
the answer with hand-tuned heuristics so demos and CI work without
external network access.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.core.config import settings
from app.services.llm import AnthropicClient, LLMUnavailableError


logger = logging.getLogger(__name__)


VISA_EVAL_SYSTEM_PROMPT = """You are a {country} visa officer evaluating a
Pakistani student's interview answer. The question was: "{question}". The
student answered: "{answer}".

Evaluate strictly but fairly. Pakistani students often struggle with:
- Clearly articulating ties to Pakistan (family, job offer, property).
- Explaining sponsor finances without sounding unconvincing.
- Balancing genuine ambition abroad with credible intent to return.
- Avoiding phrases that sound memorized.

Return strict JSON:
{{
  "clarity_score": 1-5,
  "confidence_score": 1-5,
  "relevance_score": 1-5,
  "red_flags": ["list any concerns"],
  "missing_elements": ["what was not said but should have been"],
  "what_was_good": "brief praise",
  "ideal_answer_summary": "what a strong answer would include",
  "overall_score": 1-5
}}

Do not include any prose outside of the JSON object."""


_RED_FLAG_PATTERNS = (
    (r"\bstay\s+(?:in\s+)?(?:the\s+)?(?:us|usa|uk|canada|germany)\b.*\b(?:forever|permanently)\b",
     "Mentions intent to stay permanently — visa officers read this as immigration intent."),
    (r"\b(?:forever|permanently)\b.*\bstay\b",
     "Mentions intent to stay permanently — visa officers read this as immigration intent."),
    (r"\bsettle\s+(?:in|down\s+in)\s+(?:the\s+)?(?:us|usa|uk|canada|germany)\b",
     "Explicit settlement intent — flagged as immigration risk."),
    (r"\b(?:not|no plan to|don'?t plan to|won'?t)\s+(?:return|go back)\s+to\s+(?:pakistan|home)\b",
     "Explicit statement about not returning to Pakistan."),
    (r"\bbetter\s+(?:life|opportunities)\s+(?:in|outside)\s+(?:america|usa|uk|canada|germany)\b",
     "Frames the visa as escape rather than education."),
    (r"\bi\s+(?:don'?t|do not)\s+(?:know|remember)\b",
     "Cannot recall a basic fact — confidence concern."),
    (r"\b(?:family|brother|sister|uncle|cousins?)\s+(?:lives?|is)\s+in\s+(?:the\s+)?(?:us|usa|uk|canada|germany)\b",
     "Foreign-based family raises the bar for proof of ties back home."),
)

_TIES_KEYWORDS = ("family", "parents", "job", "return", "pakistan", "home", "property", "business")
_FINANCE_KEYWORDS = ("sponsor", "bank", "father", "income", "loan", "savings", "scholarship", "funds")


def evaluate_answer_deterministic(
    *,
    country: str,
    question_text: str,
    category: str,
    answer_text: str,
) -> dict[str, Any]:
    answer = (answer_text or "").strip()
    answer_lower = answer.lower()
    words = [w for w in re.findall(r"\w+", answer_lower) if w]
    n_words = len(words)

    clarity = 5 if 25 <= n_words <= 120 else 4 if 15 <= n_words <= 200 else 2 if n_words < 8 else 3
    confidence = 4
    if any(filler in answer_lower for filler in ("um", "uh", "i don't know", "maybe", "probably")):
        confidence = 2
    elif n_words < 10:
        confidence = 2
    elif n_words > 35:
        confidence = 5

    # Relevance keyed off category
    relevance = 3
    if category == "ties" and any(k in answer_lower for k in _TIES_KEYWORDS):
        relevance = 5
    elif category == "finances" and any(k in answer_lower for k in _FINANCE_KEYWORDS):
        relevance = 5
    elif category == "motivation" and any(k in answer_lower for k in ("because", "research", "program", "field", "career")):
        relevance = 4
    elif category == "program" and any(k in answer_lower for k in ("university", "professor", "course", "research", "lab")):
        relevance = 4
    elif n_words >= 20:
        relevance = 4

    red_flags = []
    for pattern, message in _RED_FLAG_PATTERNS:
        if re.search(pattern, answer_lower):
            red_flags.append(message)

    missing: list[str] = []
    if category == "ties" and not any(k in answer_lower for k in ("family", "pakistan", "return", "home", "job")):
        missing.append("Specific ties to Pakistan (family, job, property) that ensure you return.")
    if category == "finances" and not any(k in answer_lower for k in _FINANCE_KEYWORDS):
        missing.append("A concrete funding source and the amount available.")
    if category == "program" and "research" not in answer_lower and "course" not in answer_lower:
        missing.append("A specific course, lab, or research interest at the university.")

    overall = round((clarity + confidence + relevance) / 3)
    overall = max(1, min(5, overall))
    if red_flags:
        overall = max(1, overall - 1)

    what_was_good = (
        "Direct response that addresses the question without filler."
        if n_words >= 12
        else "Brief and on-topic."
    )
    ideal_summary = (
        "A strong answer combines one specific personal fact, one direct programme link, "
        "and one calibrated reference to Pakistan ties — under 90 seconds when spoken."
    )

    return {
        "clarity_score": int(clarity),
        "confidence_score": int(confidence),
        "relevance_score": int(relevance),
        "overall_score": int(overall),
        "red_flags": red_flags,
        "missing_elements": missing,
        "what_was_good": what_was_good,
        "ideal_answer_summary": ideal_summary,
        "used_llm": False,
    }


def evaluate_answer(
    *,
    country: str,
    question_text: str,
    category: str,
    answer_text: str,
    llm: AnthropicClient | None = None,
) -> dict[str, Any]:
    client = llm or AnthropicClient()
    if not client.available:
        return evaluate_answer_deterministic(
            country=country,
            question_text=question_text,
            category=category,
            answer_text=answer_text,
        )
    try:
        data = client.call_json(
            system_prompt=VISA_EVAL_SYSTEM_PROMPT.format(
                country=country, question=question_text, answer=answer_text
            ),
            user_prompt="Return only the JSON object specified.",
            model=settings.ANTHROPIC_MODEL_FAST,
            max_tokens=900,
            temperature=0.1,
        )
    except (LLMUnavailableError, Exception):  # pragma: no cover - network failures
        return evaluate_answer_deterministic(
            country=country,
            question_text=question_text,
            category=category,
            answer_text=answer_text,
        )

    return _normalise_rubric(data)


def _normalise_rubric(data: dict[str, Any]) -> dict[str, Any]:
    def _clamp_int(value, lo=1, hi=5) -> int:
        try:
            return max(lo, min(hi, int(value)))
        except (TypeError, ValueError):
            return 3

    return {
        "clarity_score": _clamp_int(data.get("clarity_score")),
        "confidence_score": _clamp_int(data.get("confidence_score")),
        "relevance_score": _clamp_int(data.get("relevance_score")),
        "overall_score": _clamp_int(data.get("overall_score")),
        "red_flags": [str(x) for x in (data.get("red_flags") or []) if x],
        "missing_elements": [str(x) for x in (data.get("missing_elements") or []) if x],
        "what_was_good": str(data.get("what_was_good") or "").strip()
        or "Addresses the question directly.",
        "ideal_answer_summary": str(data.get("ideal_answer_summary") or "").strip()
        or "A strong answer combines one specific fact, one direct program link, and one calibrated tie to Pakistan.",
        "used_llm": True,
    }
