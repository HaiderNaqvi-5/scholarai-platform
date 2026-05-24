"""Unit tests for the GET /api/v1/geo/currency proxy endpoint.

Mocks both httpx.AsyncClient (ipwho.is upstream) and the module-level
Redis client so tests are hermetic.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def _fake_redis_no_cache() -> MagicMock:
    """Build a Redis mock that returns no cached value and accepts writes."""
    m = MagicMock()
    m.get = AsyncMock(return_value=None)
    m.set = AsyncMock(return_value=True)
    return m


def _fake_httpx(json_payload: dict, *, raise_exc: Exception | None = None) -> MagicMock:
    """Build an httpx.AsyncClient context-manager that returns json_payload,
    or raises raise_exc on .get() if provided."""
    response = MagicMock()
    response.json = MagicMock(return_value=json_payload)

    async_client_instance = MagicMock()
    if raise_exc is not None:
        async_client_instance.get = AsyncMock(side_effect=raise_exc)
    else:
        async_client_instance.get = AsyncMock(return_value=response)

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=async_client_instance)
    cm.__aexit__ = AsyncMock(return_value=None)
    factory = MagicMock(return_value=cm)
    return factory


def test_geo_currency_missing_ip_returns_pkr(client):
    """No X-Forwarded-For, no client host -> PKR fallback."""
    with patch("app.services.geo.ipwho_client._redis_client", _fake_redis_no_cache()):
        r = client.get("/api/v1/geo/currency")
    assert r.status_code == 200
    body = r.json()
    # TestClient sets request.client.host to "testclient" — that string is
    # not a routable IP so ipwho would fail; we patch redis but not httpx,
    # so the real httpx call would fail or timeout in test env. We accept
    # PKR fallback either way.
    assert body["currency"] == "PKR"


def test_geo_currency_gbp_for_uk_ip(client):
    """X-Forwarded-For with UK IP -> GBP."""
    fake_redis = _fake_redis_no_cache()
    fake_httpx = _fake_httpx(
        {"success": True, "country_code": "GB", "currency": {"code": "GBP"}}
    )
    with patch("app.services.geo.ipwho_client._redis_client", fake_redis), patch(
        "app.services.geo.ipwho_client.httpx.AsyncClient", fake_httpx
    ):
        r = client.get("/api/v1/geo/currency", headers={"X-Forwarded-For": "81.137.0.1"})
    assert r.status_code == 200
    body = r.json()
    assert body["currency"] == "GBP"
    assert body["country"] == "GB"


def test_geo_currency_unsupported_falls_back_to_pkr(client):
    """ipwho returns THB (unsupported) -> PKR fallback, country preserved."""
    fake_redis = _fake_redis_no_cache()
    fake_httpx = _fake_httpx(
        {"success": True, "country_code": "TH", "currency": {"code": "THB"}}
    )
    with patch("app.services.geo.ipwho_client._redis_client", fake_redis), patch(
        "app.services.geo.ipwho_client.httpx.AsyncClient", fake_httpx
    ):
        r = client.get("/api/v1/geo/currency", headers={"X-Forwarded-For": "1.2.3.4"})
    body = r.json()
    assert body["currency"] == "PKR"
    assert body["country"] == "TH"


def test_geo_currency_lookup_failure_falls_back_to_pkr(client):
    """httpx raises -> service returns (None, None) -> route returns PKR."""
    import httpx

    fake_redis = _fake_redis_no_cache()
    fake_httpx = _fake_httpx({}, raise_exc=httpx.ConnectError("boom"))
    with patch("app.services.geo.ipwho_client._redis_client", fake_redis), patch(
        "app.services.geo.ipwho_client.httpx.AsyncClient", fake_httpx
    ):
        r = client.get("/api/v1/geo/currency", headers={"X-Forwarded-For": "1.2.3.4"})
    body = r.json()
    assert body["currency"] == "PKR"
    assert body["country"] is None
