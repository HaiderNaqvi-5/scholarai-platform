from typing import Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RecommendationEvaluationUser, RecommendationUser
from app.schemas import (
    RecommendationBenchmarkEvaluationResponse,
    RecommendationBenchmarkListResponse,
    RecommendationEvaluationRequest,
    RecommendationEvaluationResponse,
    RecommendationListResponse,
    RecommendationRequest,
)
from app.schemas.recommendations import (
    RecommendationBenchmarkAggregate,
    RecommendationBenchmarkCaseResult,
    RecommendationBenchmarkGatePassRateItem,
    RecommendationKPIGateItem,
    RecommendationMetricItem,
    RecommendationResponseMeta,
)
from app.services.recommendations import RecommendationEvaluationService, RecommendationService
from app.services.recommendations.benchmark_registry import (
    RecommendationBenchmarkDatasetNotFoundError,
    RecommendationBenchmarkRegistry,
    RecommendationBenchmarkRegistryError,
)
from app.services.recommendations.evaluation import RecommendationMetricResult, RecommendationMetricThreshold
from app.services.kpi_policy import (
    get_recommendation_default_thresholds,
    get_recommendation_kpi_policy_version,
)
from app.services.kpi_snapshot_service import KPISnapshotService
from app.services.students import StudentService
from scholarai_common.errors import ErrorCode, ScholarAIException

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=RecommendationListResponse)
async def build_recommendations(
    payload: RecommendationRequest,
    current_user: RecommendationUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationListResponse:
    student_service = StudentService(db)
    profile = await student_service.get_profile(current_user.id)
    if profile is None:
        logger.info("recommendations_profile_missing user_id=%s", current_user.id)
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
    snapshot_service = KPISnapshotService(db)
    metric_results = service.evaluate(
        predicted_ids=payload.predicted_ids,
        judged_relevance=payload.judged_relevance,
        k_values=payload.k_values,
    )
    threshold_models = [
        RecommendationMetricThreshold(
            k=threshold.k,
            precision_at_k_min=threshold.precision_at_k_min,
            recall_at_k_min=threshold.recall_at_k_min,
            ndcg_at_k_min=threshold.ndcg_at_k_min,
            ndcg_delta_min=threshold.ndcg_delta_min,
        )
        for threshold in payload.thresholds
    ]
    if not threshold_models:
        threshold_models = get_recommendation_default_thresholds()
    baseline_metric_results = [
        RecommendationMetricResult(
            k=metric.k,
            precision_at_k=metric.precision_at_k,
            recall_at_k=metric.recall_at_k,
            ndcg_at_k=metric.ndcg_at_k,
        )
        for metric in payload.baseline_metrics
    ]

    kpi_gates = service.evaluate_kpi_gates(
        metrics=metric_results,
        thresholds=threshold_models,
        baseline_metrics=baseline_metric_results,
    )

    kpi_passed = all(gate.all_passed for gate in kpi_gates) if threshold_models else None
    policy_version = get_recommendation_kpi_policy_version()

    if kpi_passed is not None:
        await snapshot_service.record_recommendation_snapshot(
            user_id=current_user.id,
            policy_version=policy_version,
            kpi_passed=kpi_passed,
            metrics_payload=[
                {
                    "k": metric.k,
                    "precision_at_k": metric.precision_at_k,
                    "recall_at_k": metric.recall_at_k,
                    "ndcg_at_k": metric.ndcg_at_k,
                }
                for metric in metric_results
            ],
            gates_payload=[
                {
                    "k": gate.k,
                    "precision_at_k_pass": gate.precision_at_k_pass,
                    "recall_at_k_pass": gate.recall_at_k_pass,
                    "ndcg_at_k_pass": gate.ndcg_at_k_pass,
                    "ndcg_delta_pass": gate.ndcg_delta_pass,
                    "ndcg_delta_value": gate.ndcg_delta_value,
                    "all_passed": gate.all_passed,
                }
                for gate in kpi_gates
            ],
        )

    return RecommendationEvaluationResponse(
        metrics=[
            RecommendationMetricItem(
                k=metric.k,
                precision_at_k=metric.precision_at_k,
                recall_at_k=metric.recall_at_k,
                ndcg_at_k=metric.ndcg_at_k,
                mrr_at_k=metric.mrr_at_k,
            )
            for metric in metric_results
        ],
        kpi_gates=[
            RecommendationKPIGateItem(
                k=gate.k,
                precision_at_k_pass=gate.precision_at_k_pass,
                recall_at_k_pass=gate.recall_at_k_pass,
                ndcg_at_k_pass=gate.ndcg_at_k_pass,
                ndcg_delta_pass=gate.ndcg_delta_pass,
                ndcg_delta_value=gate.ndcg_delta_value,
                all_passed=gate.all_passed,
            )
            for gate in kpi_gates
        ],
        kpi_passed=kpi_passed,
        policy_version=policy_version,
        metric_set="precision_at_k,recall_at_k,ndcg_at_k",
        pipeline_version="recommendations.phase1.v1",
    )


@router.get("/benchmarks", response_model=RecommendationBenchmarkListResponse)
async def list_recommendation_benchmarks(
    current_user: RecommendationEvaluationUser,
) -> RecommendationBenchmarkListResponse:
    del current_user
    registry = RecommendationBenchmarkRegistry()
    try:
        datasets = registry.list_datasets()
    except RecommendationBenchmarkRegistryError as exc:
        logger.error("Failed to load recommendation benchmarks: %s", exc, exc_info=True)
        raise ScholarAIException(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="Failed to load recommendation benchmarks.",
            status_code=500,
        ) from exc

    policy_version = get_recommendation_kpi_policy_version()
    items = [
        {
            "dataset_id": dataset.dataset_id,
            "version": dataset.version,
            "title": dataset.title,
            "frozen_at": dataset.frozen_at,
            "case_count": len(dataset.cases),
            "k_values": dataset.k_values,
            "policy_version": policy_version,
        }
        for dataset in datasets
    ]
    return RecommendationBenchmarkListResponse(items=items, total=len(items))


@router.post(
    "/benchmarks/{dataset_id}/evaluate",
    response_model=RecommendationBenchmarkEvaluationResponse,
)
async def evaluate_recommendation_benchmark(
    dataset_id: str,
    current_user: RecommendationEvaluationUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationBenchmarkEvaluationResponse:
    registry = RecommendationBenchmarkRegistry()
    evaluation_service = RecommendationEvaluationService()
    snapshot_service = KPISnapshotService(db)

    try:
        dataset = registry.get_dataset(dataset_id)
    except RecommendationBenchmarkDatasetNotFoundError as exc:
        raise ScholarAIException(
            code=ErrorCode.NOT_FOUND,
            message=f"Benchmark dataset '{dataset_id}' not found.",
            status_code=404,
        ) from exc
    except RecommendationBenchmarkRegistryError as exc:
        logger.error(
            "Failed to load recommendation benchmark dataset '%s': %s",
            dataset_id,
            exc,
            exc_info=True,
        )
        raise ScholarAIException(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="Failed to load benchmark dataset.",
            status_code=500,
        ) from exc

    if dataset.thresholds:
        threshold_models = [
            RecommendationMetricThreshold(
                k=item.k,
                precision_at_k_min=item.precision_at_k_min,
                recall_at_k_min=item.recall_at_k_min,
                ndcg_at_k_min=item.ndcg_at_k_min,
                ndcg_delta_min=item.ndcg_delta_min,
            )
            for item in dataset.thresholds
        ]
    else:
        logger.warning(
            "Dataset %s has no KPI thresholds defined; falling back to default recommendation thresholds.",
            dataset_id,
        )
        threshold_models = get_recommendation_default_thresholds()
    baseline_metrics = [
        RecommendationMetricResult(
            k=item.k,
            precision_at_k=item.precision_at_k,
            recall_at_k=item.recall_at_k,
            ndcg_at_k=item.ndcg_at_k,
        )
        for item in dataset.baseline_metrics
    ]

    case_results: list[RecommendationBenchmarkCaseResult] = []
    metrics_by_case: list[list[RecommendationMetricResult]] = []
    gate_counts: dict[int, int] = {}
    pass_count = 0

    for case in dataset.cases:
        metric_results = evaluation_service.evaluate(
            predicted_ids=case.predicted_ids,
            judged_relevance=case.judged_relevance,
            k_values=dataset.k_values,
        )
        kpi_gates = evaluation_service.evaluate_kpi_gates(
            metrics=metric_results,
            thresholds=threshold_models,
            baseline_metrics=baseline_metrics,
        )
        case_passed = all(gate.all_passed for gate in kpi_gates) if kpi_gates else True
        if case_passed:
            pass_count += 1
        for gate in kpi_gates:
            if gate.all_passed:
                gate_counts[gate.k] = gate_counts.get(gate.k, 0) + 1

        case_results.append(
            RecommendationBenchmarkCaseResult(
                case_id=case.case_id,
                profile_label=case.profile_label,
                metrics=[
                    RecommendationMetricItem(
                        k=item.k,
                        precision_at_k=item.precision_at_k,
                        recall_at_k=item.recall_at_k,
                        ndcg_at_k=item.ndcg_at_k,
                        mrr_at_k=item.mrr_at_k,
                    )
                    for item in metric_results
                ],
                kpi_gates=[
                    RecommendationKPIGateItem(
                        k=gate.k,
                        precision_at_k_pass=gate.precision_at_k_pass,
                        recall_at_k_pass=gate.recall_at_k_pass,
                        ndcg_at_k_pass=gate.ndcg_at_k_pass,
                        ndcg_delta_pass=gate.ndcg_delta_pass,
                        ndcg_delta_value=gate.ndcg_delta_value,
                        all_passed=gate.all_passed,
                    )
                    for gate in kpi_gates
                ],
                kpi_passed=case_passed,
            )
        )
        metrics_by_case.append(metric_results)

    average_metrics = evaluation_service.aggregate_metrics(metrics_by_case)
    case_count = len(case_results)
    aggregate = RecommendationBenchmarkAggregate(
        case_count=case_count,
        pass_count=pass_count,
        pass_rate=round(pass_count / case_count, 4) if case_count else 0.0,
        average_metrics=[
            RecommendationMetricItem(
                k=item.k,
                precision_at_k=item.precision_at_k,
                recall_at_k=item.recall_at_k,
                ndcg_at_k=item.ndcg_at_k,
                mrr_at_k=item.mrr_at_k,
            )
            for item in average_metrics
        ],
        gate_pass_rates=[
            RecommendationBenchmarkGatePassRateItem(
                k=k,
                pass_rate=round(gate_counts.get(k, 0) / case_count, 4) if case_count else 0.0,
            )
            for k in sorted({metric.k for metric in average_metrics})
        ],
    )

    policy_version = get_recommendation_kpi_policy_version()
    kpi_passed = pass_count == case_count if case_count else True
    await snapshot_service.record_recommendation_snapshot(
        user_id=current_user.id,
        policy_version=policy_version,
        kpi_passed=kpi_passed,
        metrics_payload=[
            {
                "k": item.k,
                "precision_at_k": item.precision_at_k,
                "recall_at_k": item.recall_at_k,
                "ndcg_at_k": item.ndcg_at_k,
            }
            for item in average_metrics
        ],
        gates_payload=[
            {
                "k": k,
                "pass_rate": round(gate_counts.get(k, 0) / case_count, 4) if case_count else 0.0,
            }
            for k in sorted({metric.k for metric in average_metrics})
        ],
    )

    return RecommendationBenchmarkEvaluationResponse(
        dataset_id=dataset.dataset_id,
        version=dataset.version,
        title=dataset.title,
        policy_version=policy_version,
        metric_set="precision_at_k,recall_at_k,ndcg_at_k",
        pipeline_version="recommendations.phase1.v1",
        case_results=case_results,
        aggregate=aggregate,
    )
