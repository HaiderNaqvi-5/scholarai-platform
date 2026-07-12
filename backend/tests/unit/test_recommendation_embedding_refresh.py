from datetime import datetime, timezone
import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models import RecordState
from app.services.recommendations.embedding_refresh import (
    PublishedScholarshipEmbeddingRefresher,
)

pytest.importorskip("celery")
from app.tasks import recommendation_tasks



class ScalarResult:
    def __init__(self, all_items=None):
        self.all_items = all_items or []

    def scalars(self):
        return self

    def all(self):
        return self.all_items


class FakeSession:
    def __init__(self, scholarships):
        self.scholarships = scholarships
        self.added = []
        self.deleted = []
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, statement):
        visit_name = getattr(statement, "__visit_name__", "")
        if visit_name == "select":
            return ScalarResult(self.scholarships)
        if visit_name == "delete":
            self.deleted.append(statement)
            return None
        raise AssertionError(f"Unexpected statement type: {visit_name}")

    def add(self, instance):
        self.added.append(instance)

    async def flush(self):
        return None

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class FakeSplitter:
    def __init__(self, chunks):
        self.chunks = chunks

    def split_text(self, _text):
        return list(self.chunks)


class FakeEmbedder:
    def encode(self, text, **kwargs):
        return [float(len(text))]


class FakeRetriever:
    def __init__(self):
        self.index_calls = []

    async def create_index_if_not_exists(self):
        return None

    async def index_scholarship(self, scholarship, embedding):
        self.index_calls.append((scholarship.id, embedding))


def make_scholarship(*, source_key: str = "ubc-grad-funding"):
    return SimpleNamespace(
        id=uuid4(),
        title="UBC MDS Excellence Entrance Award",
        provider_name="University of British Columbia",
        country_code="CA",
        summary="Entrance funding for high-performing students.",
        funding_summary="Partial tuition offset.",
        source_url="https://example.com/scholarship",
        field_tags=["data science", "analytics"],
        degree_levels=["MS"],
        citizenship_rules=[],
        deadline_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
        record_state=RecordState.PUBLISHED,
        published_at=datetime(2026, 2, 4, tzinfo=timezone.utc),
        source_registry=SimpleNamespace(
            source_key=source_key,
            display_name=source_key.upper(),
            base_url=f"https://{source_key}.example.com",
        ),
    )


async def test_refresh_embeddings_rebuilds_chunks_and_indexes_published_records():
    scholarship = make_scholarship()
    session = FakeSession([scholarship])
    retriever = FakeRetriever()

    refresher = PublishedScholarshipEmbeddingRefresher(
        session,
        text_splitter=FakeSplitter(["alpha", "beta"]),
        embedder=FakeEmbedder(),
        retriever=retriever,
    )

    result = await refresher.refresh_published_scholarships()

    assert result["processed"] == 1
    assert result["refreshed"] == 1
    assert result["total_chunks"] == 2
    assert result["embedded_chunks"] == 2
    assert result["indexed"] == 1
    assert result["chunked_without_embeddings"] == 0
    assert len(session.deleted) == 1
    assert len(session.added) == 2
    assert all(chunk.embedding is not None for chunk in session.added)
    assert retriever.index_calls == [(scholarship.id, [273.0])]
    assert session.commits == 1
    assert session.rollbacks == 0


async def test_refresh_embeddings_falls_back_when_embedder_is_unavailable():
    scholarship = make_scholarship()
    session = FakeSession([scholarship])
    retriever = FakeRetriever()

    refresher = PublishedScholarshipEmbeddingRefresher(
        session,
        text_splitter=FakeSplitter(["fallback chunk"]),
        embedder=None,
        retriever=retriever,
    )

    result = await refresher.refresh_published_scholarships()

    assert result["processed"] == 1
    assert result["refreshed"] == 1
    assert result["total_chunks"] == 1
    assert result["embedded_chunks"] == 0
    assert result["chunked_without_embeddings"] == 1
    assert result["indexed"] == 0
    assert len(session.added) == 1
    assert session.added[0].embedding is None
    assert retriever.index_calls == []
    assert session.commits == 1


async def test_refresh_embeddings_defers_daad_records_without_touching_storage():
    scholarship = make_scholarship(source_key="daad")
    session = FakeSession([scholarship])

    refresher = PublishedScholarshipEmbeddingRefresher(
        session,
        text_splitter=FakeSplitter(["unused"]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
    )

    result = await refresher.refresh_published_scholarships()

    assert result["processed"] == 0
    assert result["deferred_daad"] == 1
    assert result["refreshed"] == 0
    assert session.deleted == []
    assert session.added == []
    assert session.commits == 0


async def test_refresh_task_invokes_async_pipeline(monkeypatch):
    session = object()

    class FakeSessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeRefresher:
        def __init__(self, db):
            assert db is session

        async def refresh_published_scholarships(self, limit=None):
            return {"limit": limit, "status": "ok"}

    monkeypatch.setattr(
        recommendation_tasks,
        "async_session_factory",
        lambda: FakeSessionContext(),
    )
    monkeypatch.setattr(
        recommendation_tasks,
        "PublishedScholarshipEmbeddingRefresher",
        FakeRefresher,
    )

    result = await asyncio.to_thread(
        recommendation_tasks.refresh_published_scholarship_embeddings,
        limit=7,
    )

    assert result == {"limit": 7, "status": "ok"}


async def test_refresh_skips_when_document_hash_unchanged():
    scholarship = make_scholarship()
    # First run: no stored hash yet -> full embed, hash gets stamped on the object.
    session = FakeSession([scholarship])
    refresher = PublishedScholarshipEmbeddingRefresher(
        session,
        text_splitter=FakeSplitter(["alpha", "beta"]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
    )
    first = await refresher.refresh_published_scholarships()
    assert first["processed"] == 1
    assert first["refreshed"] == 1
    assert first["skipped_unchanged"] == 0
    stamped = scholarship.embedding_source_hash
    assert isinstance(stamped, str) and len(stamped) == 64

    # Second run: same scholarship object already carries chunks + matching hash -> skip.
    scholarship.chunks = list(session.added)  # chunks exist, so skip is safe
    session2 = FakeSession([scholarship])
    refresher2 = PublishedScholarshipEmbeddingRefresher(
        session2,
        text_splitter=FakeSplitter(["alpha", "beta"]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
    )
    second = await refresher2.refresh_published_scholarships()
    assert second["processed"] == 0
    assert second["skipped_unchanged"] == 1
    assert second["refreshed"] == 0
    assert session2.deleted == []
    assert session2.added == []
    assert session2.commits == 0
    assert scholarship.embedding_source_hash == stamped


async def test_refresh_reembeds_when_document_text_changes():
    scholarship = make_scholarship()
    scholarship.embedding_source_hash = "0" * 64  # stale hash from a prior run
    scholarship.chunks = [SimpleNamespace(id=uuid4())]  # had chunks, but text changed
    session = FakeSession([scholarship])
    refresher = PublishedScholarshipEmbeddingRefresher(
        session,
        text_splitter=FakeSplitter(["alpha", "beta"]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
    )
    result = await refresher.refresh_published_scholarships()
    assert result["processed"] == 1
    assert result["refreshed"] == 1
    assert result["skipped_unchanged"] == 0
    assert len(session.deleted) == 1
    assert len(session.added) == 2
    assert scholarship.embedding_source_hash != "0" * 64


async def test_refresh_reembeds_when_hash_matches_but_no_chunks_exist():
    # Guards the cold-backfill case: hash present but chunk rows missing must NOT skip.
    scholarship = make_scholarship()
    session = FakeSession([scholarship])
    text = PublishedScholarshipEmbeddingRefresher(
        session, text_splitter=None, embedder=None, retriever=None
    )._build_document_text(scholarship)
    import hashlib
    scholarship.embedding_source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    scholarship.chunks = []  # matching hash but zero chunks -> must re-embed
    refresher = PublishedScholarshipEmbeddingRefresher(
        session,
        text_splitter=FakeSplitter(["alpha", "beta"]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
    )
    result = await refresher.refresh_published_scholarships()
    assert result["processed"] == 1
    assert result["skipped_unchanged"] == 0
    assert len(session.added) == 2


async def test_refresh_skips_when_lock_already_held(monkeypatch):
    session = object()

    class FakeSessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class ShouldNotRunRefresher:
        def __init__(self, db):  # pragma: no cover - must never be constructed
            raise AssertionError("refresher must not run while the dedup lock is held")

        async def refresh_published_scholarships(self, limit=None):  # pragma: no cover
            raise AssertionError("refresh must not run while the dedup lock is held")

    class FakeRedisLockHeld:
        async def set(self, key, value, *, nx=False, ex=None):
            # NX set fails (returns None) because another run already holds it.
            return None

        async def delete(self, *keys):
            return 0

    monkeypatch.setattr(
        recommendation_tasks, "async_session_factory", lambda: FakeSessionContext()
    )
    monkeypatch.setattr(
        recommendation_tasks,
        "PublishedScholarshipEmbeddingRefresher",
        ShouldNotRunRefresher,
    )
    monkeypatch.setattr(recommendation_tasks, "_redis_client", FakeRedisLockHeld())

    result = await asyncio.to_thread(
        recommendation_tasks.refresh_published_scholarship_embeddings
    )

    assert result == {"status": "skipped", "reason": "recent_run_present"}


async def test_refresh_acquires_lock_runs_then_releases(monkeypatch):
    session = object()
    events = {"set": [], "deleted": []}

    class FakeSessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeRefresher:
        def __init__(self, db):
            assert db is session

        async def refresh_published_scholarships(self, limit=None):
            return {"status": "ok", "limit": limit, "refreshed": 3}

    class FakeRedisFree:
        async def set(self, key, value, *, nx=False, ex=None):
            events["set"].append((key, nx, ex))
            return True  # NX set succeeds: lock acquired.

        async def delete(self, *keys):
            events["deleted"].extend(keys)
            return len(keys)

    monkeypatch.setattr(
        recommendation_tasks, "async_session_factory", lambda: FakeSessionContext()
    )
    monkeypatch.setattr(
        recommendation_tasks, "PublishedScholarshipEmbeddingRefresher", FakeRefresher
    )
    monkeypatch.setattr(recommendation_tasks, "_redis_client", FakeRedisFree())

    result = await asyncio.to_thread(
        recommendation_tasks.refresh_published_scholarship_embeddings,
        limit=5,
    )

    assert result == {"status": "ok", "limit": 5, "refreshed": 3}
    assert events["set"] == [
        (recommendation_tasks._EMBEDDING_REFRESH_LOCK_KEY, True, recommendation_tasks.EMBEDDING_REFRESH_LOCK_TTL_SECONDS)
    ]
    # Lock released after a successful run so the next admin enqueue can proceed.
    assert events["deleted"] == [recommendation_tasks._EMBEDDING_REFRESH_LOCK_KEY]


async def test_encode_text_passes_normalize_embeddings_true():
    """_encode_text must pass normalize_embeddings=True to match the query-side normalization."""
    encode_kwargs = {}

    class RecordingEmbedder:
        def encode(self, text, **kwargs):
            encode_kwargs.update(kwargs)
            return [1.0]

    scholarship = make_scholarship()
    session = FakeSession([scholarship])

    refresher = PublishedScholarshipEmbeddingRefresher(
        session,
        text_splitter=FakeSplitter(["chunk one"]),
        embedder=RecordingEmbedder(),
        retriever=FakeRetriever(),
    )

    await refresher.refresh_published_scholarships()

    assert encode_kwargs.get("normalize_embeddings") is True, (
        "encode() must receive normalize_embeddings=True so document embeddings "
        "live in the same space as L2-normalized query embeddings"
    )
