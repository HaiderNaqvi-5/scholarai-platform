from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RecommendationEvaluationUser, RecommendationUser
from app.schemas import (
    RecommendationEvaluationRequest,
    RecommendationEvaluationResponse,
    RecommendationListResponse,
    RecommendationRequest,
)
from app.schemas.recommendations import RecommendationResponseMeta
from app.services.recommendations import RecommendationEvaluationService, RecommendationService
from app.services.students import StudentService

router = APIRouter()


@router.post("", response_model=RecommendationListResponse)
async def build_recommendations(
    payload: RecommendationRequest,
    current_user: RecommendationUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationListResponse:
    student_service = StudentService(db)
    profile = await student_service.get_profile(current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complete your student profile first",
        )

    service = RecommendationService(db)
    items = await service.build_for_profile(profile, limit=payload.limit)
    return RecommendationListResponse(
        items=items,
        total=len(items),
        meta=RecommendationResponseMeta(
            scope_policy="canada_first",
            allowed_country_codes=["CA"],
            exception_policy="US_fulbright_only",
            pipeline_version="recommendations.phase1.v1",
        ),
    )


@router.post("/evaluate", response_model=RecommendationEvaluationResponse)
async def evaluate_recommendations(
    payload: RecommendationEvaluationRequest,
    current_user: RecommendationEvaluationUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationEvaluationResponse:
    service = RecommendationEvaluationService()
    metric_results = service.evaluate(
        predicted_ids=payload.predicted_ids,
        judged_relevance=payload.judged_relevance,
        k_values=payload.k_values,
    )
    return RecommendationEvaluationResponse(
        metrics=[
            {
                "k": metric.k,
                "precision_at_k": metric.precision_at_k,
                "recall_at_k": metric.recall_at_k,
                "ndcg_at_k": metric.ndcg_at_k,
            }
            for metric in metric_results
        ],
        metric_set="precision_at_k,recall_at_k,ndcg_at_k",
        pipeline_version="recommendations.phase1.v1",
    )
