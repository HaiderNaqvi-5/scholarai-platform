import pytest

from app.services.recommendations.service import RecommendationService

pytestmark = pytest.mark.asyncio


async def test_pgvector_candidate_retrieval_reports_rules_only_fallback_when_embeddings_are_missing(monkeypatch):
    service = RecommendationService(db=None)
    monkeypatch.setattr(service, "_encode_query", lambda _query: None)

    candidates, failure_reason = await service._retrieve_pgvector_candidates(
        search_query="target field Data Science | degree ms",
        limit=8,
    )

    assert candidates == []
    assert failure_reason == (
        "Embeddings are unavailable, so ranking fell back to published-rule heuristics only."
    )
