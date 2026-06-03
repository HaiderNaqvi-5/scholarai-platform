"""Unit tests for the visa interview simulator (Feature 8)."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from app.demo.visa_questions import (
    VISA_INTERVIEW_QUESTION_BANK,
    VISA_TYPE_BY_COUNTRY,
)
from app.services.llm import AnthropicClient
from app.services.visa_interview.evaluator import (
    VISA_EVAL_SYSTEM_PROMPT,
    evaluate_answer,
    evaluate_answer_deterministic,
    _normalise_rubric,
)


def test_question_bank_totals_match_prd():
    by_country = {}
    for q in VISA_INTERVIEW_QUESTION_BANK:
        by_country.setdefault(q["country"], 0)
        by_country[q["country"]] += 1
    assert by_country == {"GB": 20, "US": 20, "CA": 15, "DE": 15}
    assert len(VISA_INTERVIEW_QUESTION_BANK) == 70


def test_every_question_has_required_fields():
    for q in VISA_INTERVIEW_QUESTION_BANK:
        assert q["country"] in VISA_TYPE_BY_COUNTRY
        assert q["visa_type"] == VISA_TYPE_BY_COUNTRY[q["country"]]
        assert q["category"] in {"motivation", "finances", "ties", "program", "future_plans"}
        assert q["question_text"]
        assert q["difficulty"] in {"easy", "medium", "hard"}


def test_evaluator_flags_intent_to_stay_permanently():
    result = evaluate_answer_deterministic(
        country="US",
        question_text="Do you plan to return to Pakistan?",
        category="ties",
        answer_text="I want to stay in the USA permanently and bring my family.",
    )
    assert result["red_flags"]
    assert result["overall_score"] <= 3


def test_evaluator_rewards_specific_ties_answer():
    result = evaluate_answer_deterministic(
        country="GB",
        question_text="What ties do you have to Pakistan?",
        category="ties",
        answer_text=(
            "My parents and younger sister live in Karachi. I have a signed return-of-service "
            "agreement with my Pakistani employer who has held my position for the duration."
        ),
    )
    assert result["relevance_score"] == 5
    assert result["overall_score"] >= 4
    assert result["red_flags"] == []


def test_evaluator_flags_short_unconfident_answer():
    result = evaluate_answer_deterministic(
        country="DE",
        question_text="How will you fund your studies?",
        category="finances",
        answer_text="I don't know exactly. Maybe my father.",
    )
    assert result["confidence_score"] <= 2
    assert "Cannot recall" in " ".join(result["red_flags"]) or result["missing_elements"]


def test_evaluator_missing_specific_fields_in_program_answer():
    result = evaluate_answer_deterministic(
        country="CA",
        question_text="Why this specific Canadian university?",
        category="program",
        answer_text="I just like this university because it is good.",
    )
    assert any("course" in m or "lab" in m or "research" in m for m in result["missing_elements"])


def test_normalise_rubric_clamps_scores_to_range():
    raw = {
        "clarity_score": 99,
        "confidence_score": -5,
        "relevance_score": "not a number",
        "overall_score": 7,
        "red_flags": ["x", None, "y"],
        "missing_elements": "should be list",
        "what_was_good": "",
        "ideal_answer_summary": "",
    }
    norm = _normalise_rubric(raw)
    assert 1 <= norm["clarity_score"] <= 5
    assert 1 <= norm["confidence_score"] <= 5
    assert 1 <= norm["relevance_score"] <= 5
    assert 1 <= norm["overall_score"] <= 5
    assert norm["red_flags"] == ["x", "y"]
    # missing_elements parsed defensively
    assert isinstance(norm["missing_elements"], list)
    assert norm["used_llm"] is True


def test_evaluator_returns_int_scores_in_range():
    result = evaluate_answer_deterministic(
        country="GB",
        question_text="Why do you want to study in the UK?",
        category="motivation",
        answer_text=(
            "Because the research culture in fluid dynamics is strongest in the UK and I want to "
            "work with Professor X at the University of Manchester whose papers on turbulence "
            "modelling I have followed since my final-year project."
        ),
    )
    for key in ("clarity_score", "confidence_score", "relevance_score", "overall_score"):
        assert isinstance(result[key], int)
        assert 1 <= result[key] <= 5
    assert result["used_llm"] is False


class _BurnCapResult:
    def scalar_one(self) -> int:
        return 0


class _CaptureDB:
    """Async DB stub: burn-cap SUM returns 0; record_llm add/flush no-ops."""

    def __init__(self) -> None:
        self.added: list = []

    async def execute(self, _statement):
        return _BurnCapResult()

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        return None


def _user():
    return SimpleNamespace(id=uuid.uuid4(), plan="elite", plan_currency="PKR")


async def test_visa_evaluator_keeps_system_prompt_static_and_caches():
    captured: list[dict] = []

    rubric_json = (
        '{"clarity_score": 4, "confidence_score": 4, "relevance_score": 4, '
        '"overall_score": 4, "red_flags": [], "missing_elements": [], '
        '"what_was_good": "ok", "ideal_answer_summary": "ok"}'
    )
    stub_message = SimpleNamespace(
        content=[SimpleNamespace(text=rubric_json)],
        usage=SimpleNamespace(input_tokens=120, output_tokens=40),
    )

    def _fake_raw_call(self, **kwargs):  # noqa: ANN001 - matches method shape
        captured.append(kwargs)
        return stub_message

    llm = AnthropicClient()
    llm._api_key = "test-key"  # noqa: SLF001 - force the live-SDK branch
    AnthropicClient._raw_call = _fake_raw_call  # noqa: SLF001 - SDK seam swap

    try:
        await evaluate_answer(
            db=_CaptureDB(),
            user=_user(),
            country="US",
            question_text="Why this university?",
            category="program",
            answer_text="Because of Professor X's turbulence lab at MIT.",
            llm=llm,
        )
        await evaluate_answer(
            db=_CaptureDB(),
            user=_user(),
            country="GB",
            question_text="What ties do you have to Pakistan?",
            category="ties",
            answer_text="My parents and sister live in Karachi.",
            llm=llm,
        )
    finally:
        del AnthropicClient._raw_call  # restore the real bound method

    assert len(captured) == 2
    first, second = captured

    # System block is the static rubric constant verbatim — identical across
    # both calls, so the ephemeral prompt cache can hit on the second call.
    assert first["system_prompt"] == VISA_EVAL_SYSTEM_PROMPT
    assert second["system_prompt"] == first["system_prompt"]

    # The static block must NOT carry any per-call values.
    assert "{country}" not in VISA_EVAL_SYSTEM_PROMPT
    assert "US" not in VISA_EVAL_SYSTEM_PROMPT
    assert "Karachi" not in VISA_EVAL_SYSTEM_PROMPT
    assert "Professor X" not in VISA_EVAL_SYSTEM_PROMPT

    # The per-call country/question/answer now live in the user prompt.
    assert "US" in first["user_prompt"]
    assert "Why this university?" in first["user_prompt"]
    assert "Professor X" in first["user_prompt"]
    assert "GB" in second["user_prompt"]
    assert "Karachi" in second["user_prompt"]
