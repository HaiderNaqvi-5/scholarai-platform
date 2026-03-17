from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RecordState, Scholarship, StudentProfile
from app.schemas.recommendations import RecommendationItem
from app.services.recommendations.eligibility import MatchEvaluation, evaluate_match, normalize_gpa
import os


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Load XGBoost Explainer
        model_path = os.path.join(os.path.dirname(__file__), "../../../models/xgboost_model.json")
        try:
            from ai_services.evaluation.explainer import ShapExplainer
            self.explainer = ShapExplainer(model_path)
        except Exception as e:
            print(f"Warning: Failed to load SHAP Explainer: {e}")
            self.explainer = None

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

            fit_score = evaluation.score
            shap_output = None
            
            # Stage 3: XGBoost Reranking if explainer is loaded and GPA exists
            if self.explainer and profile.gpa_value:
                gpa = normalize_gpa(profile.gpa_value, profile.gpa_scale) or 3.2
                ielts = profile.ielts_score or 7.0
                research = profile.research_score or 5.0
                volunteer = profile.volunteer_score or 2.0
                match_val = 8.0 if evaluation.score > 0.6 else 4.0
                
                try:
                    explanation = self.explainer.explain_prediction({
                        "gpa": gpa,
                        "ielts_score": ielts,
                        "research_score": research,
                        "volunteer_score": volunteer,
                        "program_match_score": match_val,
                    })
                    fit_score = explanation["prediction_probability"]
                    shap_output = explanation["contributions"]
                except Exception:
                    pass

            fit_band = _fit_band(fit_score)
            recommendations.append(
                RecommendationItem(
                    scholarship_id=str(scholarship.id),
                    title=scholarship.title,
                    provider_name=scholarship.provider_name,
                    country_code=scholarship.country_code,
                    deadline_at=scholarship.deadline_at,
                    record_state=scholarship.record_state.value,
                    estimated_fit_score=fit_score,
                    fit_band=fit_band,
                    match_summary=_build_match_summary(fit_band, evaluation),
                    matched_criteria=evaluation.matched_criteria,
                    constraint_notes=evaluation.constraint_notes,
                    top_reasons=evaluation.matched_criteria[:3],
                    warnings=evaluation.constraint_notes,
                    shap_explanation=shap_output,
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
