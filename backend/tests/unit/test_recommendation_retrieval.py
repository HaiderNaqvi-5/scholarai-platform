import threading

import pytest

import app.services.recommendations.service as service_module
from app.services.recommendations.service import (
    RecommendationService,
    _get_shared_embedder,
)


class _FakeEmbedder:
    """Stand-in for SentenceTransformer that records load count and call thread."""

    load_count = 0

    def __init__(self, model_name):
        type(self).load_count += 1
        self.model_name = model_name

    def encode(self, text, normalize_embeddings=False):
        # Record the thread .encode() runs on so the test can assert it is
        # offloaded off the event-loop thread.
        _FakeEmbedder.last_encode_thread = threading.current_thread()

        class _Vector:
            def tolist(self_inner):
                return [0.1, 0.2, 0.3]

        return _Vector()


async def test_embedder_is_a_process_wide_singleton_across_instances(monkeypatch):
    _get_shared_embedder.cache_clear()
    _FakeEmbedder.load_count = 0
    monkeypatch.setattr(service_module, "SentenceTransformer", _FakeEmbedder)

    first = RecommendationService(db=None)
    second = RecommendationService(db=None)

    vec_a = await first._encode_query("target field Data Science | degree ms")
    vec_b = await second._encode_query("target field Physics | degree phd")

    assert vec_a == [0.1, 0.2, 0.3]
    assert vec_b == [0.1, 0.2, 0.3]
    # Loaded once total, not once per RecommendationService instance.
    assert _FakeEmbedder.load_count == 1
    _get_shared_embedder.cache_clear()


async def test_encode_query_runs_encode_off_the_event_loop(monkeypatch):
    _get_shared_embedder.cache_clear()
    _FakeEmbedder.load_count = 0
    monkeypatch.setattr(service_module, "SentenceTransformer", _FakeEmbedder)

    loop_thread = threading.current_thread()
    service = RecommendationService(db=None)

    vec = await service._encode_query("target field Data Science | degree ms")

    assert vec == [0.1, 0.2, 0.3]
    # .encode() must NOT run on the event-loop thread (threadpool offload).
    assert _FakeEmbedder.last_encode_thread is not loop_thread
    _get_shared_embedder.cache_clear()


async def test_encode_query_returns_none_when_model_unavailable(monkeypatch):
    _get_shared_embedder.cache_clear()
    monkeypatch.setattr(service_module, "SentenceTransformer", None)

    service = RecommendationService(db=None)
    assert await service._encode_query("anything") is None
    _get_shared_embedder.cache_clear()


async def test_pgvector_candidate_retrieval_reports_rules_only_fallback_when_embeddings_are_missing(monkeypatch):
    service = RecommendationService(db=None)

    async def _fake_encode(_query):
        return None

    monkeypatch.setattr(service, "_encode_query", _fake_encode)

    candidates, failure_reason = await service._retrieve_pgvector_candidates(
        search_query="target field Data Science | degree ms",
        limit=8,
    )

    assert candidates == []
    assert failure_reason == (
        "Embeddings are unavailable, so ranking fell back to published-rule heuristics only."
    )
