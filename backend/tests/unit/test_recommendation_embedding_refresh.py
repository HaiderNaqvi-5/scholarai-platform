from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models import RecordState
from app.services.recommendations.embedding_refresh import (
    PublishedScholarshipEmbeddingRefresher,
)

pytest.importorskip("celery")
from app.tasks import recommendation_tasks


pytestmark = pytest.mark.asyncio


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
    def encode(self, text):
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

    result = recommendation_tasks.refresh_published_scholarship_embeddings(limit=7)

    assert result == {"limit": 7, "status": "ok"}
