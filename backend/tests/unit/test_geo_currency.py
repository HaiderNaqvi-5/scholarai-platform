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


def test_client_ip_ignores_xff_when_trusted_proxy_hops_zero(monkeypatch):
    """TRUSTED_PROXY_HOPS=0 -> spoofed X-Forwarded-For is ignored; socket peer
    (request.client.host) wins. Mirrors rate_limit.py:_client_ip gating."""
    from app.api.v1.routes.geo import _client_ip
    from app.core.config import settings

    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 0)
    request = MagicMock()
    request.headers = {"x-forwarded-for": "203.0.113.42"}
    request.client = MagicMock(host="10.0.0.5")
    assert _client_ip(request) == "10.0.0.5"


def test_client_ip_honors_xff_when_trusted_proxy_hops_positive(monkeypatch):
    """TRUSTED_PROXY_HOPS>0 -> left-most X-Forwarded-For entry is trusted."""
    from app.api.v1.routes.geo import _client_ip
    from app.core.config import settings

    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
    request = MagicMock()
    request.headers = {"x-forwarded-for": "203.0.113.42, 10.0.0.1"}
    request.client = MagicMock(host="10.0.0.5")
    assert _client_ip(request) == "203.0.113.42"


def test_geo_currency_missing_ip_returns_null(client):
    """No X-Forwarded-For, no client host -> currency=null, country=null.
    Frontend will then map via defaultCurrencyForCountry (-> PKR for null cc).
    """
    with patch("app.services.geo.ipwho_client._redis_client", _fake_redis_no_cache()):
        r = client.get("/api/v1/geo/currency")
    assert r.status_code == 200
    body = r.json()
    # TestClient sets request.client.host to "testclient" — that string is
    # not a routable IP so ipwho would fail; we patch redis but not httpx,
    # so the real httpx call would fail. Result: currency=null.
    assert body["currency"] is None


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


def test_geo_currency_unsupported_returns_null_keeps_country(client):
    """ipwho returns THB (unsupported) -> currency=null, country=TH preserved.
    Frontend maps TH -> regional default via defaultCurrencyForCountry.
    """
    fake_redis = _fake_redis_no_cache()
    fake_httpx = _fake_httpx(
        {"success": True, "country_code": "TH", "currency": {"code": "THB"}}
    )
    with patch("app.services.geo.ipwho_client._redis_client", fake_redis), patch(
        "app.services.geo.ipwho_client.httpx.AsyncClient", fake_httpx
    ):
        r = client.get("/api/v1/geo/currency", headers={"X-Forwarded-For": "1.2.3.4"})
    body = r.json()
    assert body["currency"] is None
    assert body["country"] == "TH"


def test_geo_currency_lookup_failure_returns_null(client):
    """httpx raises -> service returns (None, None) -> route returns null/null."""
    import httpx

    fake_redis = _fake_redis_no_cache()
    fake_httpx = _fake_httpx({}, raise_exc=httpx.ConnectError("boom"))
    with patch("app.services.geo.ipwho_client._redis_client", fake_redis), patch(
        "app.services.geo.ipwho_client.httpx.AsyncClient", fake_httpx
    ):
        r = client.get("/api/v1/geo/currency", headers={"X-Forwarded-For": "1.2.3.4"})
    body = r.json()
    assert body["currency"] is None
    assert body["country"] is None


# GEO-IP-LEAK: raw IP must not be persisted (Redis key) or logged pre-consent.
def test_redact_ip_stable_and_irreversible():
    from app.services.geo.ipwho_client import _redact_ip

    ip = "203.0.113.42"
    assert _redact_ip(ip) == _redact_ip(ip)  # stable -> cache still hits
    assert ip not in _redact_ip(ip)
    assert _redact_ip(ip) != _redact_ip("198.51.100.7")


def test_cache_key_hashes_ip_no_raw_ip_leak():
    from app.services.geo.ipwho_client import _cache_key, _redact_ip

    ip = "203.0.113.42"
    key = _cache_key(ip)
    assert ip not in key
    assert key == f"geo:currency:{_redact_ip(ip)}"


def test_redis_cache_uses_hashed_key_not_raw_ip(client):
    """Neither the cache read nor write may carry the raw IP as the key."""
    fake_redis = _fake_redis_no_cache()
    fake_httpx = _fake_httpx(
        {"success": True, "country_code": "GB", "currency": {"code": "GBP"}}
    )
    ip = "81.137.0.99"
    with patch("app.services.geo.ipwho_client._redis_client", fake_redis), patch(
        "app.services.geo.ipwho_client.httpx.AsyncClient", fake_httpx
    ):
        r = client.get("/api/v1/geo/currency", headers={"X-Forwarded-For": ip})
    assert r.status_code == 200
    calls = list(fake_redis.get.await_args_list) + list(fake_redis.set.await_args_list)
    assert calls, "expected redis get/set to be exercised"
    for call in calls:
        assert ip not in str(call)
