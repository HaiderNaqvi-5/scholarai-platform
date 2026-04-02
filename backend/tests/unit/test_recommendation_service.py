from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models import DegreeLevel, RecordState
from app.services.recommendations import RecommendationService
from app.services.recommendations.eligibility import evaluate_match
from app.services.recommendations.service import (
    RERANK_POLICY_VERSION,
    RetrievedCandidate,
    _compose_recommendation_score,
    _distance_to_similarity,
)

pytestmark = pytest.mark.asyncio


class FakeRowsResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return list(self._rows)


class FakeQuerySession:
    def __init__(self, rows):
        self.rows = list(rows)
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return FakeRowsResult(self.rows)


async def no_db_candidates(*, limit, exclude_ids):
    assert limit >= 0
    assert isinstance(exclude_ids, set)
    return []


def make_profile(**overrides):
    data = {
        "id": uuid4(),
        "citizenship_country_code": "PK",
        "gpa_value": Decimal("3.70"),
        "gpa_scale": Decimal("4.0"),
        "target_field": "Data Science",
        "target_degree_level": DegreeLevel.MS,
        "target_country_code": "CA",
        "language_test_type": None,
        "language_test_score": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_scholarship(**overrides):
    now = datetime.now(timezone.utc)
    data = {
        "id": uuid4(),
        "title": "UBC MDS Excellence Entrance Award",
        "provider_name": "University of British Columbia",
        "country_code": "CA",
        "deadline_at": now + timedelta(days=21),
        "published_at": now - timedelta(days=7),
        "record_state": RecordState.PUBLISHED,
        "source_url": "https://example.com/ubc-mds-award",
        "summary": "Entrance funding for strong master's applicants.",
        "field_tags": ["data science", "analytics"],
        "degree_levels": ["MS"],
        "citizenship_rules": [],
        "min_gpa_value": Decimal("3.30"),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


async def test_recommendation_service_enforces_eligible_only_invariant(monkeypatch):
    profile = make_profile()
    eligible = make_scholarship(title="Eligible award")
    citizenship_mismatch = make_scholarship(
        title="Citizenship mismatch",
        citizenship_rules=["US"],
    )
    gpa_mismatch = make_scholarship(
        title="GPA mismatch",
        min_gpa_value=Decimal("4.00"),
    )

    service = RecommendationService(db=None)

    async def fake_vector_candidates(*, search_query, limit):
        assert "target field Data Science" in search_query
        assert limit == 60
        return [
            RetrievedCandidate(eligible, "pgvector_chunk_similarity", 0.88),
            RetrievedCandidate(citizenship_mismatch, "pgvector_chunk_similarity", 0.82),
        ], None

    async def fake_db_candidates(*, limit, exclude_ids):
        assert limit == 58
        assert exclude_ids == {eligible.id, citizenship_mismatch.id}
        return [RetrievedCandidate(gpa_mismatch, "published_rules_db_fallback", None)]

    monkeypatch.setattr(service, "_retrieve_pgvector_candidates", fake_vector_candidates)
    monkeypatch.setattr(service, "_retrieve_db_candidates", fake_db_candidates)

    items = await service.build_for_profile(profile, limit=10)

    assert [item.scholarship_id for item in items] == [str(eligible.id)]
    assert items[0].retrieval_source == "pgvector_chunk_similarity"
    assert items[0].semantic_similarity == pytest.approx(0.88)
    assert items[0].record_state == "published"


async def test_pgvector_candidate_retrieval_preserves_distance_order(monkeypatch):
    first = make_scholarship(title="First scholarship")
    second = make_scholarship(title="Second scholarship")
    session = FakeQuerySession(
        [
            SimpleNamespace(scholarship_id=second.id, best_distance=0.4),
            SimpleNamespace(scholarship_id=first.id, best_distance=0.9),
        ]
    )
    service = RecommendationService(db=session)

    monkeypatch.setattr(service, "_encode_query", lambda _query: [0.25, 0.75])

    async def fake_load_scholarships_by_ids(scholarship_ids):
        assert scholarship_ids == [second.id, first.id]
        return {
            first.id: first,
            second.id: second,
        }

    monkeypatch.setattr(service, "_load_scholarships_by_ids", fake_load_scholarships_by_ids)

    candidates, failure_reason = await service._retrieve_pgvector_candidates(
        search_query="target field Data Science | degree ms",
        limit=5,
    )

    assert failure_reason is None
    assert len(session.statements) == 1
    assert [candidate.scholarship.id for candidate in candidates] == [second.id, first.id]
    assert [candidate.semantic_similarity for candidate in candidates] == [
        _distance_to_similarity(0.4),
        _distance_to_similarity(0.9),
    ]
    assert all(candidate.retrieval_source == "pgvector_chunk_similarity" for candidate in candidates)


async def test_recommendation_service_keeps_heuristic_ranking_when_embeddings_are_unavailable(monkeypatch):
    profile = make_profile()
    now = datetime.now(timezone.utc)
    strongest = make_scholarship(
        title="Beta strongest",
        field_tags=["data science", "machine learning"],
        deadline_at=now + timedelta(days=10),
        min_gpa_value=Decimal("3.20"),
    )
    medium = make_scholarship(
        title="Alpha medium",
        field_tags=["analytics"],
        deadline_at=now + timedelta(days=35),
        min_gpa_value=Decimal("3.50"),
    )
    weakest = make_scholarship(
        title="Gamma weakest",
        field_tags=["economics"],
        deadline_at=now + timedelta(days=120),
        min_gpa_value=None,
    )
    fallback_reason = "Embeddings are unavailable, so ranking fell back to published-rule heuristics only."

    service = RecommendationService(db=None)

    async def fake_vector_candidates(*, search_query, limit):
        assert "citizenship PK" in search_query
        assert limit == 60
        return [], fallback_reason

    async def fake_db_candidates(*, limit, exclude_ids):
        assert limit == 60
        assert exclude_ids == set()
        return [
            RetrievedCandidate(weakest, "published_rules_db_fallback", None),
            RetrievedCandidate(medium, "published_rules_db_fallback", None),
            RetrievedCandidate(strongest, "published_rules_db_fallback", None),
        ]

    monkeypatch.setattr(service, "_retrieve_pgvector_candidates", fake_vector_candidates)
    monkeypatch.setattr(service, "_retrieve_db_candidates", fake_db_candidates)

    items = await service.build_for_profile(profile, limit=10)

    expected_by_id = {}
    for scholarship in (strongest, medium, weakest):
        evaluation = evaluate_match(profile, scholarship)
        assert evaluation is not None
        score, factors = _compose_recommendation_score(
            evaluation=evaluation,
            semantic_similarity=None,
        )
        expected_by_id[str(scholarship.id)] = {
            "score": score,
            "factors": factors,
        }

    expected_ids = [
        str(scholarship.id)
        for scholarship in sorted(
            (strongest, medium, weakest),
            key=lambda scholarship: (
                -expected_by_id[str(scholarship.id)]["score"],
                scholarship.deadline_at.isoformat(),
                scholarship.title,
            ),
        )
    ]

    assert [item.scholarship_id for item in items] == expected_ids
    assert [item.estimated_fit_score for item in items] == [
        expected_by_id[scholarship_id]["score"] for scholarship_id in expected_ids
    ]
    assert all(item.semantic_similarity is None for item in items)
    assert all(item.fallback_reason == fallback_reason for item in items)
    assert all(
        item.match_summary.endswith("Ranking used rules only because embeddings were unavailable.")
        for item in items
    )
    assert all(item.rationale is not None for item in items)
    assert all(item.rationale.stages.retrieval.status == "fallback" for item in items)
    assert all(
        "retrieval_fallback" in {factor.code for factor in item.rationale.stages.retrieval.factors}
        for item in items
    )


async def test_recommendation_service_explanation_payload_matches_ranking_features(monkeypatch):
    profile = make_profile()
    scholarship = make_scholarship(
        title="Explainable award",
        field_tags=["data science", "analytics"],
        min_gpa_value=Decimal("3.20"),
    )
    semantic_similarity = 0.73

    service = RecommendationService(db=None)

    async def fake_vector_candidates(*, search_query, limit):
        assert "target country CA" in search_query
        assert limit == 30
        return [
            RetrievedCandidate(
                scholarship,
                "pgvector_chunk_similarity",
                semantic_similarity,
            )
        ], None

    monkeypatch.setattr(service, "_retrieve_pgvector_candidates", fake_vector_candidates)
    monkeypatch.setattr(service, "_retrieve_db_candidates", no_db_candidates)

    items = await service.build_for_profile(profile, limit=5)

    assert len(items) == 1
    item = items[0]
    evaluation = evaluate_match(profile, scholarship)
    assert evaluation is not None
    expected_score, expected_factors = _compose_recommendation_score(
        evaluation=evaluation,
        semantic_similarity=semantic_similarity,
    )

    assert item.estimated_fit_score == expected_score
    assert item.heuristic_factors == expected_factors
    assert item.semantic_similarity == pytest.approx(semantic_similarity)
    assert item.fallback_reason is None
    assert item.rerank_policy_version == RERANK_POLICY_VERSION
    assert item.rule_pass_count == evaluation.passed_rule_count
    assert item.rule_total_count == evaluation.total_rule_count
    assert item.eligibility_graph == evaluation.eligibility_graph
    assert item.rationale is not None
    assert item.rationale.summary
    assert item.rationale.stages.scope.status == "applied"
    assert item.rationale.stages.eligibility.status == "applied"
    assert item.rationale.stages.retrieval.status == "applied"
    assert item.rationale.stages.rerank.status == "applied"
    assert item.rationale.stages.explanation.status == "applied"
    assert item.signal_language is not None
    assert "Published scholarship facts" in item.signal_language.facts_label
    assert "Estimated ranking signals" in item.signal_language.estimated_signals_label
    retrieval_codes = {factor.code for factor in item.rationale.stages.retrieval.factors}
    rerank_codes = {factor.code for factor in item.rationale.stages.rerank.factors}
    assert "retrieval_source" in retrieval_codes
    assert "semantic_similarity" in retrieval_codes
    assert set(item.heuristic_factors).issubset(rerank_codes)
    assert set(item.heuristic_factors) == {
        "rule_pass_counts",
        "field_alignment",
        "country_alignment",
        "semantic_similarity",
        "gpa_alignment",
        "deadline_urgency",
    }


async def test_recommendation_score_guardrail_applies_floor(monkeypatch):
    profile = make_profile(gpa_value=Decimal("4.00"))
    weak = make_scholarship(
        title="Weak alignment award",
        field_tags=["data science"],
        degree_levels=["MS"],
        citizenship_rules=[],
        min_gpa_value=Decimal("4.00"),
        deadline_at=datetime.now(timezone.utc) + timedelta(days=730),
    )

    service = RecommendationService(db=None)

    async def fake_vector_candidates(*, search_query, limit):
        assert limit == 30
        return [RetrievedCandidate(weak, "pgvector_chunk_similarity", 0.02)], None

    monkeypatch.setattr(service, "_retrieve_pgvector_candidates", fake_vector_candidates)
    monkeypatch.setattr(service, "_retrieve_db_candidates", no_db_candidates)

    items = await service.build_for_profile(profile, limit=5)
    assert len(items) == 1
    assert items[0].estimated_fit_score >= 0.3
