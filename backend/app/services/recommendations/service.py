from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RecordState, Scholarship, StudentProfile
from app.schemas.recommendations import RecommendationItem
from app.services.recommendations.eligibility import evaluate_match


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

            score, reasons, warnings = evaluation
            recommendations.append(
                RecommendationItem(
                    scholarship_id=str(scholarship.id),
                    title=scholarship.title,
                    provider_name=scholarship.provider_name,
                    deadline_at=scholarship.deadline_at,
                    estimated_fit_score=score,
                    fit_band=_fit_band(score),
                    top_reasons=reasons[:3],
                    warnings=warnings,
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
