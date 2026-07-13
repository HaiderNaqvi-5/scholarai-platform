import pytest

pytest.importorskip("celery")

from app.api.v1.routes import recommendations


class _FakeTask:
    id = "task-abc-123"


async def test_refresh_embeddings_endpoint_enqueues_worker_task(monkeypatch):
    calls = {"count": 0}

    def fake_delay():
        calls["count"] += 1
        return _FakeTask()

    monkeypatch.setattr(
        recommendations.refresh_published_scholarship_embeddings,
        "delay",
        fake_delay,
    )

    result = await recommendations.refresh_recommendation_embeddings(
        current_user=object()
    )

    assert result == {"status": "queued", "task_id": "task-abc-123"}
    assert calls["count"] == 1
