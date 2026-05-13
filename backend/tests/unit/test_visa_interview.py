"""Unit tests for the visa interview simulator (Feature 8)."""

from __future__ import annotations

from app.demo.visa_questions import (
    VISA_INTERVIEW_QUESTION_BANK,
    VISA_TYPE_BY_COUNTRY,
)
from app.services.visa_interview.evaluator import (
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
