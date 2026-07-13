"""Task 40: /readyz must return HTTP 503 (status code, not just a body
field) when the DB or Redis probe fails, so load balancers gating on
status code correctly see "unhealthy". /livez stays process-only (never
probes DB/Redis, always 200).
"""

from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient

from app import main as main_module


class _RaisingDBSession:
    async def execute(self, *args, **kwargs):
        raise RuntimeError("db down")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _OKDBSession:
    async def execute(self, *args, **kwargs):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _db_factory(session):
    @asynccontextmanager
    async def _factory():
        yield session

    return _factory


class _RaisingRedis:
    async def ping(self):
        raise RuntimeError("redis down")


class _OKRedis:
    async def ping(self):
        return True


def test_readyz_returns_503_when_db_probe_fails(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(main_module, "async_session_factory", _db_factory(_RaisingDBSession()))
    monkeypatch.setattr(main_module, "redis_client", _OKRedis())

    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_readyz_returns_503_when_redis_probe_fails(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(main_module, "async_session_factory", _db_factory(_OKDBSession()))
    monkeypatch.setattr(main_module, "redis_client", _RaisingRedis())

    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_readyz_returns_200_when_db_and_redis_healthy(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(main_module, "async_session_factory", _db_factory(_OKDBSession()))
    monkeypatch.setattr(main_module, "redis_client", _OKRedis())

    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_livez_returns_200_regardless_of_db_state(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(main_module, "async_session_factory", _db_factory(_RaisingDBSession()))
    monkeypatch.setattr(main_module, "redis_client", _RaisingRedis())

    response = client.get("/livez")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"
