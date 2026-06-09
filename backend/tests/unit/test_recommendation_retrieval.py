import threading
import types
import uuid

import pytest
from sqlalchemy.dialects import postgresql

import app.services.recommendations.service as service_module
from app.models import RecordState
from app.services.recommendations.service import (
    RecommendationService,
    _distance_to_similarity,
)
from tests.conftest import requires_db


def _compiled_sql(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    ).lower()


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
    service_module._SHARED_EMBEDDER = None
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
    service_module._SHARED_EMBEDDER = None


async def test_encode_query_runs_encode_off_the_event_loop(monkeypatch):
    service_module._SHARED_EMBEDDER = None
    _FakeEmbedder.load_count = 0
    monkeypatch.setattr(service_module, "SentenceTransformer", _FakeEmbedder)

    loop_thread = threading.current_thread()
    service = RecommendationService(db=None)

    vec = await service._encode_query("target field Data Science | degree ms")

    assert vec == [0.1, 0.2, 0.3]
    # .encode() must NOT run on the event-loop thread (threadpool offload).
    assert _FakeEmbedder.last_encode_thread is not loop_thread
    service_module._SHARED_EMBEDDER = None


async def test_encode_query_returns_none_when_model_unavailable(monkeypatch):
    service_module._SHARED_EMBEDDER = None
    monkeypatch.setattr(service_module, "SentenceTransformer", None)

    service = RecommendationService(db=None)
    assert await service._encode_query("anything") is None
    service_module._SHARED_EMBEDDER = None


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


def test_pgvector_retrieval_is_chunk_level_ann_without_group_by():
    # perf-db-03 option (b): the ANN query must be a per-CHUNK
    # ORDER BY embedding <=> :q LIMIT over scholarship_chunks — the shape the
    # ivfflat index ix_scholarship_chunks_embedding can serve. It must NOT use
    # func.min()/GROUP BY on the indexed column (that defeats the index), and the
    # ORDER BY must be on the chunk embedding distance, not the scholarship
    # description embedding.
    service = RecommendationService(db=None)

    stmt = service._build_pgvector_stmt(query_embedding=[0.0] * 768, limit=8)
    sql = _compiled_sql(stmt)

    assert "scholarship_chunks" in sql
    # Distance ranking is over the chunk embedding column, not the scholarship
    # description embedding.
    assert "min(" not in sql
    assert "group by" not in sql
    assert "<=>" in sql or "cosine_distance" in sql
    assert "order by" in sql
    assert "limit" in sql
    # The ORDER BY / distance projection references the chunk embedding.
    assert "scholarship_chunks.embedding" in sql


def test_pgvector_retrieval_overfetches_chunk_window_for_dedupe():
    # The chunk ANN must over-fetch limit * _CHUNK_FANOUT candidate chunks so
    # that, after dedupe-to-best-per-scholarship, >= limit distinct scholarships
    # remain. The compiled LIMIT must therefore be limit * _CHUNK_FANOUT.
    service = RecommendationService(db=None)

    limit = 8
    stmt = service._build_pgvector_stmt(query_embedding=[0.0] * 768, limit=limit)
    sql = _compiled_sql(stmt)

    assert service_module._CHUNK_FANOUT >= 2
    # LIMIT is rendered as a bind param; assert via the compiled bind value.
    compiled = stmt.compile(dialect=postgresql.dialect())
    limit_params = [
        v for k, v in compiled.params.items() if "param" in k or "limit" in k
    ]
    assert (limit * service_module._CHUNK_FANOUT) in compiled.params.values()


async def test_pgvector_retrieval_dedupes_best_chunk_per_scholarship(monkeypatch):
    # perf-db-03 option (b): the chunk ANN returns several chunk rows per
    # scholarship, pre-sorted by ascending distance. The method must dedupe to
    # the BEST (smallest-distance) chunk per scholarship IN PYTHON, preserving
    # ascending order — reproducing the old func.min()/GROUP BY semantics — and
    # label the source pgvector_chunk_similarity.
    sch_a = uuid.uuid4()  # closest overall (best chunk 0.20)
    sch_b = uuid.uuid4()  # next (best chunk 0.40)
    scholarship_a = types.SimpleNamespace(
        id=sch_a, title="Chevening", provider_name="FCDO", record_state=RecordState.PUBLISHED
    )
    scholarship_b = types.SimpleNamespace(
        id=sch_b, title="Fulbright", provider_name="USEFP", record_state=RecordState.PUBLISHED
    )
    captured: dict[str, object] = {}

    # Chunk rows already ordered by ascending distance, with duplicate
    # scholarship_ids (two chunks for sch_a, two for sch_b). Dedupe must keep the
    # FIRST (smallest-distance) chunk per scholarship: A@0.20, then B@0.40.
    class _ChunkResult:
        def all(self_inner):
            return [
                types.SimpleNamespace(scholarship_id=sch_a, distance=0.20),
                types.SimpleNamespace(scholarship_id=sch_b, distance=0.40),
                types.SimpleNamespace(scholarship_id=sch_a, distance=0.55),
                types.SimpleNamespace(scholarship_id=sch_b, distance=0.70),
            ]

    class _FakeDB:
        async def execute(self_inner, stmt, *args, **kwargs):
            text = str(stmt).lower()
            if "set " in text and "ivfflat.probes" in text:
                captured["probes_set"] = True
                return _ChunkResult.__new__(_ChunkResult)
            captured["query_stmt"] = stmt
            return _ChunkResult()

    service = RecommendationService(db=_FakeDB())

    async def _fake_encode(_query):
        return [0.0] * 768

    async def _fake_load(ids):
        captured["loaded_ids"] = list(ids)
        return {sch_a: scholarship_a, sch_b: scholarship_b}

    monkeypatch.setattr(service, "_encode_query", _fake_encode)
    monkeypatch.setattr(service, "_load_scholarships_by_ids", _fake_load)

    candidates, failure_reason = await service._retrieve_pgvector_candidates(
        search_query="target field Data Science | degree ms",
        limit=8,
    )

    assert failure_reason is None
    assert captured.get("probes_set") is True
    # Best-chunk-per-scholarship, ascending distance: A (0.20) then B (0.40).
    assert [c.scholarship.id for c in candidates] == [sch_a, sch_b]
    assert captured["loaded_ids"] == [sch_a, sch_b]
    assert [c.semantic_similarity for c in candidates] == [
        _distance_to_similarity(0.20),
        _distance_to_similarity(0.40),
    ]
    assert all(c.retrieval_source == "pgvector_chunk_similarity" for c in candidates)


@requires_db
async def test_chunk_ann_best_chunk_ordering_against_real_pgvector(db_session):
    # End-to-end on real Postgres+pgvector: seed one published scholarship with
    # two chunks (a far chunk and a near chunk) and a second published
    # scholarship whose single chunk sits between them. The chunk ANN + Python
    # dedupe must (1) return the FIRST scholarship via its NEAR chunk (best
    # distance), proving min-per-scholarship semantics, and (2) order the two
    # scholarships by their best chunk distance.
    from app.models import RecordState
    from app.models.models import Scholarship, ScholarshipChunk

    # Query vector points at e0; near chunks share that axis, far chunks are on e1.
    query_vec = [1.0] + [0.0] * 767
    near_vec = [0.95] + [0.0] * 767  # tiny cosine distance to query
    mid_vec = [0.5, 0.5] + [0.0] * 766  # moderate distance
    far_vec = [0.0, 1.0] + [0.0] * 766  # orthogonal -> ~1.0 distance

    sch_near = Scholarship(
        title="Near scholarship",
        country_code="PK",
        source_url="https://example.test/near",
        record_state=RecordState.PUBLISHED,
    )
    sch_mid = Scholarship(
        title="Mid scholarship",
        country_code="PK",
        source_url="https://example.test/mid",
        record_state=RecordState.PUBLISHED,
    )
    db_session.add_all([sch_near, sch_mid])
    await db_session.flush()

    db_session.add_all(
        [
            # sch_near owns BOTH a far chunk and a near chunk; dedupe must pick near.
            ScholarshipChunk(
                scholarship_id=sch_near.id, chunk_index=0, content_text="far", embedding=far_vec
            ),
            ScholarshipChunk(
                scholarship_id=sch_near.id, chunk_index=1, content_text="near", embedding=near_vec
            ),
            ScholarshipChunk(
                scholarship_id=sch_mid.id, chunk_index=0, content_text="mid", embedding=mid_vec
            ),
        ]
    )
    await db_session.commit()

    service = RecommendationService(db=db_session)

    async def _fake_encode(_query):
        return query_vec

    service._encode_query = _fake_encode  # type: ignore[method-assign]

    candidates, failure_reason = await service._retrieve_pgvector_candidates(
        search_query="anything", limit=5
    )

    assert failure_reason is None
    # Best chunk per scholarship -> sch_near (via its near chunk) ranks first,
    # then sch_mid. sch_near must appear exactly once despite owning two chunks.
    assert [c.scholarship.id for c in candidates] == [sch_near.id, sch_mid.id]
    assert all(c.retrieval_source == "pgvector_chunk_similarity" for c in candidates)
    # near chunk distance < mid chunk distance -> higher similarity first.
    assert candidates[0].semantic_similarity > candidates[1].semantic_similarity
