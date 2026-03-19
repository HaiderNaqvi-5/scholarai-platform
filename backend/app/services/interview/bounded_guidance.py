from statistics import mean
from typing import Any

from app.schemas.interviews import InterviewAnswerFeedback
from app.services.interview.prompts import get_prompts_for_category

DIMENSION_PRIORITY = ("clarity", "relevance", "confidence", "specificity")

GENERAL_QUESTION_SET = [
    "Tell us about yourself and what led you to pursue graduate study in data science or analytics.",
    "Describe a project or experience that shows how you solve problems under uncertainty.",
    "Why would you be a strong fit for a scholarship that values academic promise and future impact?",
]

SCHOLARSHIP_MODE_QUESTION_SET = [
    "Why are you applying to this scholarship pathway now, and how does it fit your next academic step?",
    "Describe one example that proves you can turn scholarship support into measurable academic or community impact.",
    "What specific preparation do you already have that makes you a credible scholarship candidate?",
]


def build_question_set(practice_mode: str, scholarships: list[Any]) -> list[str]:
    if practice_mode != "scholarship":
        return list(GENERAL_QUESTION_SET)
    if not scholarships:
        return list(SCHOLARSHIP_MODE_QUESTION_SET)

    primary = scholarships[0]
    prompt_context = get_prompts_for_category(primary.category or "general")
    field_text = ", ".join(primary.field_tags[:2]) if primary.field_tags else "your intended field"
    provider_text = primary.provider_name or primary.title
    funding_text = primary.funding_summary or "the support attached to this opportunity"
    theme_text = ", ".join(prompt_context["themes"][:2])

    return [
        f"Why are you specifically prepared for {primary.title} and the graduate path you want to pursue in {primary.country_code}?",
        f"This opportunity emphasizes {theme_text}. Describe a past example that proves you already work this way in {field_text}.",
        f"How would you use {funding_text} from {provider_text} to create measurable academic or community impact after graduate study?",
    ]


def build_adaptive_question(
    base_question: str,
    weakest_dimension: str | None,
    scholarships: list[Any],
) -> str:
    if not weakest_dimension:
        return base_question

    scholarship_title = scholarships[0].title if scholarships else "the grounded scholarship context"
    prefix_map = {
        "clarity": "Answer in three parts: context, evidence, and result.",
        "relevance": f"Keep the answer tightly tied to {scholarship_title} and the actual question being asked.",
        "confidence": "Use direct ownership language about what you did, decided, and learned.",
        "specificity": "Use one concrete example with an action and outcome instead of general claims.",
    }
    prefix = prefix_map.get(weakest_dimension, "Answer directly and precisely.")
    return f"{prefix} {base_question}"


def select_weakest_dimension(feedback: InterviewAnswerFeedback | dict[str, Any]) -> str | None:
    dimensions = getattr(feedback, "dimensions", None)
    if dimensions is None and isinstance(feedback, dict):
        dimensions = feedback.get("dimensions", [])
    if not dimensions:
        return None

    ranked_dimensions: list[tuple[int, int, str]] = []
    for item in dimensions:
        dimension_name = getattr(item, "dimension", None)
        dimension_score = getattr(item, "score", None)
        if isinstance(item, dict):
            dimension_name = item.get("dimension")
            dimension_score = item.get("score")
        if dimension_name is None or dimension_score is None:
            continue
        priority_index = DIMENSION_PRIORITY.index(dimension_name) if dimension_name in DIMENSION_PRIORITY else 99
        ranked_dimensions.append((int(dimension_score), priority_index, str(dimension_name)))

    if not ranked_dimensions:
        return None

    ranked_dimensions.sort()
    return ranked_dimensions[0][2]


def build_history_summary(responses: list[InterviewAnswerFeedback]) -> dict[str, Any]:
    recent_answers = []
    for response in responses[-3:]:
        weakest_dimension = select_weakest_dimension(response)
        strongest_dimension = _select_strongest_dimension(response)
        recent_answers.append(
            {
                "question_index": response.question_index,
                "question_text": response.question_text,
                "overall_score": round(response.overall_score, 2),
                "weakest_dimension": weakest_dimension,
                "strongest_dimension": strongest_dimension,
                "improvement_focus": response.improvement_prompts[0] if response.improvement_prompts else None,
            }
        )

    return {
        "answered_count": len(responses),
        "recent_answers": recent_answers,
    }


def build_trend_summary(responses: list[InterviewAnswerFeedback]) -> dict[str, Any]:
    if not responses:
        return {
            "average_score": None,
            "score_delta": None,
            "score_direction": "insufficient_data",
            "weakest_dimension_overall": None,
            "latest_weakest_dimension": None,
            "dimension_averages": {},
        }

    overall_scores = [response.overall_score for response in responses]
    dimension_buckets: dict[str, list[int]] = {}
    for response in responses:
        for dimension in response.dimensions:
            dimension_buckets.setdefault(dimension.dimension, []).append(dimension.score)

    dimension_averages = {
        key: round(mean(values), 2)
        for key, values in sorted(dimension_buckets.items())
        if values
    }
    weakest_dimension_overall = (
        min(dimension_averages.items(), key=lambda item: (item[1], DIMENSION_PRIORITY.index(item[0]) if item[0] in DIMENSION_PRIORITY else 99))[0]
        if dimension_averages
        else None
    )
    latest_weakest_dimension = select_weakest_dimension(responses[-1])

    score_delta = None
    score_direction = "insufficient_data"
    if len(overall_scores) >= 2:
        score_delta = round(overall_scores[-1] - overall_scores[0], 2)
        if score_delta >= 0.25:
            score_direction = "improving"
        elif score_delta <= -0.25:
            score_direction = "declining"
        else:
            score_direction = "steady"

    return {
        "average_score": round(mean(overall_scores), 2),
        "score_delta": score_delta,
        "score_direction": score_direction,
        "weakest_dimension_overall": weakest_dimension_overall,
        "latest_weakest_dimension": latest_weakest_dimension,
        "dimension_averages": dimension_averages,
    }


def _select_strongest_dimension(response: InterviewAnswerFeedback) -> str | None:
    if not response.dimensions:
        return None
    ranked_dimensions = sorted(
        (
            (dimension.score, -(DIMENSION_PRIORITY.index(dimension.dimension) if dimension.dimension in DIMENSION_PRIORITY else 99), dimension.dimension)
            for dimension in response.dimensions
        ),
        reverse=True,
    )
    return ranked_dimensions[0][2] if ranked_dimensions else None
