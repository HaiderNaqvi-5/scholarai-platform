from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RecordState, Scholarship, StudentProfile
from app.schemas.recommendations import RecommendationItem
from app.services.recommendations.eligibility import MatchEvaluation, evaluate_match


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_for_profile(
        self,
        profile: StudentProfile,
        limit: int = 10,
    ) -> list[RecommendationItem]:
        result = await self.db.execute(
            select(Scholarship)
            .where(Scholarship.record_state == RecordState.PUBLISHED)
            .order_by(Scholarship.deadline_at.asc().nulls_last(), Scholarship.title.asc())
        )
        scholarships = result.scalars().all()

        recommendations: list[RecommendationItem] = []
        for scholarship in scholarships:
            evaluation = evaluate_match(profile, scholarship)
            if evaluation is None:
                continue

            fit_band = _fit_band(evaluation.score)
            recommendations.append(
                RecommendationItem(
                    scholarship_id=str(scholarship.id),
                    title=scholarship.title,
                    provider_name=scholarship.provider_name,
                    country_code=scholarship.country_code,
                    deadline_at=scholarship.deadline_at,
                    record_state=scholarship.record_state.value,
                    estimated_fit_score=evaluation.score,
                    fit_band=fit_band,
                    match_summary=_build_match_summary(fit_band, evaluation),
                    matched_criteria=evaluation.matched_criteria,
                    constraint_notes=evaluation.constraint_notes,
                    top_reasons=evaluation.matched_criteria[:3],
                    warnings=evaluation.constraint_notes,
                )
            )

        recommendations.sort(
            key=lambda item: (
                -item.estimated_fit_score,
                item.deadline_at.isoformat()
                if item.deadline_at is not None
                else "9999-12-31T23:59:59+00:00",
                item.title,
            )
        )
        return recommendations[:limit]


def _fit_band(score: float) -> str:
    if score >= 0.8:
        return "strong"
    if score >= 0.55:
        return "possible"
    return "watch"


def _build_match_summary(
    fit_band: str,
    evaluation: MatchEvaluation,
) -> str:
    if fit_band == "strong":
        opening = "Strong match across the main published filters."
    elif fit_band == "possible":
        opening = "Possible match with clear baseline alignment."
    else:
        opening = "Limited-fit option worth a manual review only if it still supports your priorities."

    lead_reason = evaluation.matched_criteria[0] if evaluation.matched_criteria else (
        "This record cleared the current deterministic filter set."
    )
    if evaluation.constraint_notes:
        return f"{opening} {lead_reason} Ranking stayed conservative because {evaluation.constraint_notes[0].lower()}"

    return f"{opening} {lead_reason}"
