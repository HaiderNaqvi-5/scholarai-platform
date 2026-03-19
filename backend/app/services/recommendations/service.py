from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RecordState, Scholarship, StudentProfile
from app.models.models import ScholarshipChunk
from app.schemas.recommendations import (
    RecommendationFactor,
    RecommendationItem,
    RecommendationRationale,
    RecommendationRationaleStages,
    RecommendationStageDetail,
)
from app.services.recommendations.eligibility import (
    MatchEvaluation,
    evaluate_match,
    normalize_gpa,
)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


@dataclass(frozen=True)
class RetrievedCandidate:
    scholarship: Scholarship
    retrieval_source: str
    semantic_similarity: float | None


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._embedder = None

    async def build_for_profile(
        self,
        profile: StudentProfile,
        limit: int = 10,
    ) -> list[RecommendationItem]:
        candidate_limit = max(limit * 6, 30)
        search_query = self._build_query_text(profile)

        vector_candidates, retrieval_failure_reason = await self._retrieve_pgvector_candidates(
            search_query=search_query,
            limit=candidate_limit,
        )

        seen_ids = {candidate.scholarship.id for candidate in vector_candidates}
        db_fill_limit = max(candidate_limit - len(vector_candidates), 0)
        fallback_candidates = await self._retrieve_db_candidates(
            limit=db_fill_limit,
            exclude_ids=seen_ids,
        )

        candidates = vector_candidates + fallback_candidates
        recommendations: list[RecommendationItem] = []
        for candidate in candidates:
            evaluation = evaluate_match(profile, candidate.scholarship)
            if evaluation is None:
                continue

            fit_score, heuristic_factors = _compose_recommendation_score(
                evaluation=evaluation,
                semantic_similarity=candidate.semantic_similarity,
            )
            fit_band = _fit_band(fit_score)
            item_rules_only_fallback = candidate.semantic_similarity is None
            fallback_reason = None
            if item_rules_only_fallback:
                fallback_reason = (
                    retrieval_failure_reason
                    or "This record was ranked without semantic similarity because no scholarship embedding hit was available."
                )
            rationale = _build_rationale(
                candidate=candidate,
                evaluation=evaluation,
                heuristic_factors=heuristic_factors,
                fallback_reason=fallback_reason,
            )

            recommendations.append(
                RecommendationItem(
                    scholarship_id=str(candidate.scholarship.id),
                    title=candidate.scholarship.title,
                    provider_name=candidate.scholarship.provider_name,
                    country_code=candidate.scholarship.country_code,
                    deadline_at=candidate.scholarship.deadline_at,
                    record_state=candidate.scholarship.record_state.value,
                    estimated_fit_score=fit_score,
                    fit_band=fit_band,
                    match_summary=_build_match_summary(
                        fit_band=fit_band,
                        evaluation=evaluation,
                        rules_only_fallback=item_rules_only_fallback,
                    ),
                    matched_criteria=evaluation.matched_criteria,
                    constraint_notes=evaluation.constraint_notes,
                    top_reasons=evaluation.matched_criteria[:3],
                    warnings=evaluation.constraint_notes,
                    shap_explanation=None,
                    retrieval_source=candidate.retrieval_source,
                    semantic_similarity=candidate.semantic_similarity,
                    rule_pass_count=evaluation.passed_rule_count,
                    rule_total_count=evaluation.total_rule_count,
                    heuristic_factors=heuristic_factors,
                    fallback_reason=fallback_reason,
                    eligibility_graph=evaluation.eligibility_graph,
                    signal_language={
                        "facts_label": "Published scholarship facts",
                        "estimated_signals_label": "Estimated ranking signals",
                        "estimated_signals_notice": (
                            "Estimated ranking signals help order recommendations. "
                            "They do not state scholarship outcomes."
                        ),
                    },
                    rationale=rationale,
                )
            )

            self.logger.info(
                "recommendation.generated student=%s scholarship=%s score=%.4f source=%s rules=%s/%s semantic=%s",
                profile.id,
                candidate.scholarship.id,
                fit_score,
                candidate.retrieval_source,
                evaluation.passed_rule_count,
                evaluation.total_rule_count,
                candidate.semantic_similarity,
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

    async def _retrieve_pgvector_candidates(
        self,
        *,
        search_query: str,
        limit: int,
    ) -> tuple[list[RetrievedCandidate], str | None]:
        query_embedding = self._encode_query(search_query)
        if query_embedding is None:
            return [], "Embeddings are unavailable, so ranking fell back to published-rule heuristics only."

        distance = ScholarshipChunk.embedding.cosine_distance(query_embedding)
        stmt = (
            select(
                ScholarshipChunk.scholarship_id,
                func.min(distance).label("best_distance"),
            )
            .join(Scholarship, Scholarship.id == ScholarshipChunk.scholarship_id)
            .where(Scholarship.record_state == RecordState.PUBLISHED)
            .where(ScholarshipChunk.embedding.is_not(None))
            .group_by(ScholarshipChunk.scholarship_id)
            .order_by(func.min(distance))
            .limit(limit)
        )

        rows = (await self.db.execute(stmt)).all()
        if not rows:
            return [], "Published scholarships do not have usable chunk embeddings yet, so ranking used rules only."

        scholarship_ids = [row.scholarship_id for row in rows]
        scholarships = await self._load_scholarships_by_ids(scholarship_ids)
        best_distance_by_id = {
            row.scholarship_id: float(row.best_distance)
            for row in rows
            if row.best_distance is not None
        }

        candidates: list[RetrievedCandidate] = []
        for scholarship_id in scholarship_ids:
            scholarship = scholarships.get(scholarship_id)
            if scholarship is None:
                continue
            best_distance = best_distance_by_id.get(scholarship_id)
            candidates.append(
                RetrievedCandidate(
                    scholarship=scholarship,
                    retrieval_source="pgvector_chunk_similarity",
                    semantic_similarity=_distance_to_similarity(best_distance)
                    if best_distance is not None
                    else None,
                )
            )
        return candidates, None

    async def _retrieve_db_candidates(
        self,
        *,
        limit: int,
        exclude_ids: set[uuid.UUID],
    ) -> list[RetrievedCandidate]:
        if limit <= 0:
            return []

        scope_priority = case(
            (Scholarship.country_code == "CA", 0),
            (Scholarship.country_code == "US", 1),
            else_=2,
        )
        stmt = (
            select(Scholarship)
            .where(Scholarship.record_state == RecordState.PUBLISHED)
            .order_by(
                scope_priority,
                Scholarship.deadline_at.asc().nulls_last(),
                Scholarship.published_at.desc().nulls_last(),
                Scholarship.title.asc(),
            )
            .limit(limit + len(exclude_ids))
        )

        scholarships = (await self.db.execute(stmt)).scalars().all()
        candidates: list[RetrievedCandidate] = []
        for scholarship in scholarships:
            if scholarship.id in exclude_ids:
                continue
            candidates.append(
                RetrievedCandidate(
                    scholarship=scholarship,
                    retrieval_source="published_rules_db_fallback",
                    semantic_similarity=None,
                )
            )
            if len(candidates) >= limit:
                break
        return candidates

    async def _load_scholarships_by_ids(
        self,
        scholarship_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, Scholarship]:
        if not scholarship_ids:
            return {}

        stmt = (
            select(Scholarship)
            .where(Scholarship.id.in_(scholarship_ids))
            .where(Scholarship.record_state == RecordState.PUBLISHED)
        )
        scholarships = (await self.db.execute(stmt)).scalars().all()
        return {scholarship.id: scholarship for scholarship in scholarships}

    def _build_query_text(self, profile: StudentProfile) -> str:
        normalized_gpa = normalize_gpa(profile.gpa_value, profile.gpa_scale)
        parts = [
            f"target field {profile.target_field}",
            f"degree {profile.target_degree_level.value}",
            f"target country {profile.target_country_code}",
            f"citizenship {profile.citizenship_country_code}",
        ]
        if normalized_gpa is not None:
            parts.append(f"normalized GPA {normalized_gpa:.2f}")
        if profile.language_test_type and profile.language_test_score is not None:
            parts.append(
                f"{profile.language_test_type} score {float(profile.language_test_score):.2f}"
            )
        return " | ".join(parts)

    def _encode_query(self, search_query: str) -> list[float] | None:
        if not search_query or SentenceTransformer is None:
            return None

        if self._embedder is None:
            try:
                self._embedder = SentenceTransformer("all-mpnet-base-v2")
            except Exception as exc:
                self.logger.warning("recommendation.embedding_init_failed error=%s", exc)
                self._embedder = False

        if not self._embedder:
            return None

        try:
            return self._embedder.encode(
                search_query,
                normalize_embeddings=True,
            ).tolist()
        except Exception as exc:
            self.logger.warning("recommendation.embedding_encode_failed error=%s", exc)
            return None


def _compose_recommendation_score(
    *,
    evaluation: MatchEvaluation,
    semantic_similarity: float | None,
) -> tuple[float, dict[str, float]]:
    factors = {
        "rule_pass_counts": round(
            evaluation.passed_rule_count / max(evaluation.total_rule_count, 1),
            4,
        ),
        "field_alignment": round(evaluation.field_alignment, 4),
        "country_alignment": round(evaluation.country_alignment, 4),
        "semantic_similarity": round(semantic_similarity, 4)
        if semantic_similarity is not None
        else 0.0,
        "gpa_alignment": round(evaluation.gpa_alignment, 4),
        "deadline_urgency": round(evaluation.deadline_urgency, 4),
    }

    weights = {
        "rule_pass_counts": 0.32,
        "field_alignment": 0.18,
        "country_alignment": 0.18,
        "semantic_similarity": 0.16,
        "gpa_alignment": 0.1,
        "deadline_urgency": 0.06,
    }
    if semantic_similarity is None:
        weights.pop("semantic_similarity")

    weight_total = sum(weights.values())
    score = 0.0
    for key, weight in weights.items():
        score += factors[key] * (weight / weight_total)

    return round(min(score, 0.99), 4), factors


def _distance_to_similarity(distance: float) -> float:
    clamped = max(0.0, min(distance, 2.0))
    return round(1.0 - (clamped / 2.0), 4)


def _fit_band(score: float) -> str:
    if score >= 0.72:
        return "strong"
    if score >= 0.5:
        return "possible"
    return "watch"


def _build_match_summary(
    *,
    fit_band: str,
    evaluation: MatchEvaluation,
    rules_only_fallback: bool,
) -> str:
    if fit_band == "strong":
        opening = "Strong match across the current published rules and ranking signals."
    elif fit_band == "possible":
        opening = "Possible match with enough baseline alignment to merit a shortlist review."
    else:
        opening = "Borderline option that needs manual verification before spending application effort."

    lead_reason = evaluation.matched_criteria[0] if evaluation.matched_criteria else (
        "This record cleared the current deterministic filter set."
    )
    fallback_note = " Ranking used rules only because embeddings were unavailable." if rules_only_fallback else ""
    if evaluation.constraint_notes:
        return (
            f"{opening} {lead_reason} Ranking stayed conservative because "
            f"{evaluation.constraint_notes[0].lower()}{fallback_note}"
        )

    return f"{opening} {lead_reason}{fallback_note}"


def _build_rationale(
    *,
    candidate: RetrievedCandidate,
    evaluation: MatchEvaluation,
    heuristic_factors: dict[str, float],
    fallback_reason: str | None,
) -> RecommendationRationale:
    fact_factors: list[RecommendationFactor] = []
    scope_factors: list[RecommendationFactor] = []
    eligibility_factors: list[RecommendationFactor] = []

    for rule in evaluation.rule_results:
        stage = "scope" if rule.key in {"published", "phase_scope", "country_target"} else "eligibility"
        source = "published_record" if rule.key in {"published", "phase_scope", "country_target", "deadline"} else "validated_rule"
        if rule.key in {"citizenship", "gpa", "field_alignment", "degree_level"}:
            source = "profile_input"
        factor = RecommendationFactor(
            code=rule.key,
            label=rule.label,
            detail=rule.reason,
            stage=stage,
            source=source,  # type: ignore[arg-type]
            direction=_factor_direction(rule.status),
            numeric_value=round(float(rule.score), 4),
            display_value=(
                f"student={rule.student_value} / scholarship={rule.scholarship_value}"
                if rule.student_value or rule.scholarship_value
                else None
            ),
        )
        fact_factors.append(factor)
        if stage == "scope":
            scope_factors.append(factor)
        else:
            eligibility_factors.append(factor)

    retrieval_factors: list[RecommendationFactor] = [
        RecommendationFactor(
            code="retrieval_source",
            label="Retrieval strategy",
            detail=(
                "Semantic retrieval over published scholarship embeddings."
                if candidate.semantic_similarity is not None
                else "Rules-first fallback over published scholarships."
            ),
            stage="retrieval",
            source="retrieval_model",
            direction="supports" if candidate.semantic_similarity is not None else "neutral",
            display_value=candidate.retrieval_source,
        )
    ]
    if candidate.semantic_similarity is not None:
        retrieval_factors.append(
            RecommendationFactor(
                code="semantic_similarity",
                label="Semantic alignment",
                detail="Semantic match between your profile query and published scholarship text.",
                stage="retrieval",
                source="retrieval_model",
                direction="supports",
                numeric_value=round(candidate.semantic_similarity, 4),
            )
        )
    elif fallback_reason:
        retrieval_factors.append(
            RecommendationFactor(
                code="retrieval_fallback",
                label="Fallback applied",
                detail=fallback_reason,
                stage="retrieval",
                source="retrieval_model",
                direction="neutral",
            )
        )

    rerank_labels = {
        "rule_pass_counts": "Rule pass ratio",
        "field_alignment": "Field alignment",
        "country_alignment": "Country alignment",
        "semantic_similarity": "Semantic similarity",
        "gpa_alignment": "GPA alignment",
        "deadline_urgency": "Deadline urgency",
    }
    rerank_factors = [
        RecommendationFactor(
            code=key,
            label=rerank_labels.get(key, key.replace("_", " ").title()),
            detail="Heuristic rerank factor used to prioritize eligible recommendations.",
            stage="rerank",
            source="rerank_model",
            direction="supports" if value > 0 else "neutral",
            numeric_value=round(value, 4),
        )
        for key, value in heuristic_factors.items()
    ]

    estimated_signals = retrieval_factors + rerank_factors
    retrieval_status = "applied" if candidate.semantic_similarity is not None else "fallback"
    retrieval_summary = (
        "Retrieved via pgvector similarity over published scholarship content."
        if candidate.semantic_similarity is not None
        else "Semantic retrieval was unavailable; rules-first fallback retrieval was used."
    )

    return RecommendationRationale(
        summary=(
            "Published scholarship facts established eligibility, and estimated ranking "
            "signals ordered the shortlist."
        ),
        facts=fact_factors,
        estimated_signals=estimated_signals,
        stages=RecommendationRationaleStages(
            scope=RecommendationStageDetail(
                status="applied",
                summary="Canada-first scope checks passed for this recommendation.",
                factors=scope_factors,
            ),
            eligibility=RecommendationStageDetail(
                status="applied",
                summary="Published eligibility checks passed for this recommendation.",
                factors=eligibility_factors,
            ),
            retrieval=RecommendationStageDetail(
                status=retrieval_status,  # type: ignore[arg-type]
                summary=retrieval_summary,
                factors=retrieval_factors,
            ),
            rerank=RecommendationStageDetail(
                status="applied",
                summary="Heuristic reranking combined rule fit, alignment, and urgency factors.",
                factors=rerank_factors,
            ),
            explanation=RecommendationStageDetail(
                status="applied",
                summary="Explanation payload separates validated facts from estimated signals.",
                factors=[],
            ),
        ),
    )


def _factor_direction(status: str) -> str:
    if status == "pass":
        return "supports"
    if status == "fail":
        return "limits"
    return "neutral"
