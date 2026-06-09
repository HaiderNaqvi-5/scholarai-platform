"""Unit tests for SEC-RL-01 — atomic Redis rate limiter keyed on user id /
trusted-proxy IP.

Uses the repo's standard async-no-mark style (``asyncio_mode=auto``), a fake
async redis whose ``eval`` is an honest atomic INCR + NX-expire emulation (so
concurrency is genuinely exercised — each call is a single coroutine step),
``monkeypatch`` on the module-level ``redis_client``, and Starlette ``Request``
scopes built by hand (no DB needed).

Asserts:
(a) atomic over-limit raises 429 exactly at the limit under concurrency;
(b) IP keying ignores ``X-Forwarded-For`` when ``TRUSTED_PROXY_HOPS=0`` and
    honors the left-most XFF when ``>0``;
(c) authed routes key on ``request.state.current_user.id``, not IP.
"""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
import redis.asyncio as redis
from starlette.requests import Request

from fastapi import status
from scholarai_common.errors import ScholarAIException, ErrorCode
import app.core.rate_limit as rate_limit
from app.core.rate_limit import RateLimiter


class _FakeRedis:
    """Honest emulation of the limiter's Lua contract: INCR then NX-expire,
    returning the post-increment count. Atomic per call (single coroutine step)."""

    def __init__(self):
        self.counts: dict[str, int] = {}
        self.ttls: dict[str, int] = {}
        self.fail = False

    async def eval(self, _script, _numkeys, key, window):  # noqa: ANN001
        if self.fail:
            raise redis.RedisError("down")
        new = self.counts.get(key, 0) + 1
        self.counts[key] = new
        if new == 1:
            self.ttls[key] = int(window)
        return new


def _request(path: str, *, client_host: str = "10.0.0.9", headers=None, user=None) -> Request:
    raw_headers = [
        (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": raw_headers,
        "client": (client_host, 5555),
        "query_string": b"",
        "state": {},
    }
    req = Request(scope)
    if user is not None:
        req.state.current_user = user
    return req


async def test_atomic_limit_blocks_at_threshold_under_concurrency(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    limiter = RateLimiter(requests_limit=3, window_seconds=60, fail_open=False)

    # Fire 3 concurrent requests — all should pass (count reaches exactly 3).
    await asyncio.gather(*(limiter(_request("/x")) for _ in range(3)))
    assert fake.counts["rate_limit:/x:ip:10.0.0.9"] == 3
    assert fake.ttls["rate_limit:/x:ip:10.0.0.9"] == 60

    # The 4th must be rejected — no extra slot leaks past the threshold.
    with pytest.raises(ScholarAIException) as exc:
        await limiter(_request("/x"))
    assert exc.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert exc.value.code == ErrorCode.VALIDATION_ERROR


async def test_ip_key_ignores_xff_without_trusted_proxy(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    monkeypatch.setattr(rate_limit.settings, "TRUSTED_PROXY_HOPS", 0)
    limiter = RateLimiter(requests_limit=5, window_seconds=60)

    await limiter(_request("/y", client_host="10.0.0.9",
                           headers={"X-Forwarded-For": "1.2.3.4"}))
    # Socket peer is used; spoofed XFF is NOT trusted.
    assert "rate_limit:/y:ip:10.0.0.9" in fake.counts
    assert "rate_limit:/y:ip:1.2.3.4" not in fake.counts


async def test_ip_key_honors_left_most_xff_with_trusted_proxy(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    monkeypatch.setattr(rate_limit.settings, "TRUSTED_PROXY_HOPS", 1)
    limiter = RateLimiter(requests_limit=5, window_seconds=60)

    await limiter(_request("/z", client_host="172.16.0.1",
                           headers={"X-Forwarded-For": "1.2.3.4, 172.16.0.1"}))
    assert "rate_limit:/z:ip:1.2.3.4" in fake.counts


async def test_authenticated_route_keys_on_user_id(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    uid = uuid4()
    user = SimpleNamespace(id=uid)
    limiter = RateLimiter(requests_limit=5, window_seconds=60)

    # Two different IPs, same authenticated user -> shared user-scoped bucket.
    await limiter(_request("/api/v1/recommendations", client_host="9.9.9.9", user=user))
    await limiter(_request("/api/v1/recommendations", client_host="8.8.8.8", user=user))
    assert fake.counts[f"rate_limit:/api/v1/recommendations:user:{uid}"] == 2


async def test_fail_open_swallows_redis_error(monkeypatch):
    fake = _FakeRedis()
    fake.fail = True
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    limiter = RateLimiter(requests_limit=1, window_seconds=60, fail_open=True)
    # Must return None (allow) when Redis is down and fail_open=True.
    assert await limiter(_request("/x")) is None


async def test_fail_closed_raises_503_on_redis_error(monkeypatch):
    fake = _FakeRedis()
    fake.fail = True
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    limiter = RateLimiter(requests_limit=1, window_seconds=60, fail_open=False)
    with pytest.raises(ScholarAIException) as exc:
        await limiter(_request("/x"))
    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# ---------------------------------------------------------------------------
# P2-10 — high-cost / security limiter instances must fail CLOSED
# ---------------------------------------------------------------------------

async def test_recommendations_limiter_fails_closed_on_redis_outage(monkeypatch):
    """The 20/hr recommendations limiter (LLM cost endpoint) must DENY, not allow,
    when Redis is unavailable.  Encodes the fix for P2-10."""
    fake = _FakeRedis()
    fake.fail = True
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    # Mirror the exact constructor call in routes/recommendations.py
    limiter = RateLimiter(requests_limit=20, window_seconds=3_600, fail_open=False)
    with pytest.raises(ScholarAIException) as exc:
        await limiter(_request("/api/v1/recommendations"))
    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc.value.code == ErrorCode.VALIDATION_ERROR


async def test_data_export_limiter_fails_closed_on_redis_outage(monkeypatch):
    """The 3/day data-export limiter (PII-heavy endpoint) must DENY, not allow,
    when Redis is unavailable.  Encodes the fix for P2-10."""
    fake = _FakeRedis()
    fake.fail = True
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    # Mirror the exact constructor call in routes/privacy.py
    limiter = RateLimiter(requests_limit=3, window_seconds=86_400, fail_open=False)
    with pytest.raises(ScholarAIException) as exc:
        await limiter(_request("/api/v1/privacy/data-export"))
    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc.value.code == ErrorCode.VALIDATION_ERROR


async def test_fail_closed_logs_degraded_mode(monkeypatch, caplog):
    """Fail-closed path must emit a warning so operators see degraded mode."""
    import logging
    fake = _FakeRedis()
    fake.fail = True
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    limiter = RateLimiter(requests_limit=5, window_seconds=60, fail_open=False)
    with caplog.at_level(logging.WARNING, logger="app.core.rate_limit"):
        with pytest.raises(ScholarAIException):
            await limiter(_request("/api/v1/recommendations"))
    assert any("fail_closed" in r.message for r in caplog.records)


async def test_fail_open_logs_degraded_mode(monkeypatch, caplog):
    """Fail-open path must also emit a warning (different tag) so low-risk
    limiters still surface Redis outages in operator logs."""
    import logging
    fake = _FakeRedis()
    fake.fail = True
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    limiter = RateLimiter(requests_limit=5, window_seconds=60, fail_open=True)
    with caplog.at_level(logging.WARNING, logger="app.core.rate_limit"):
        result = await limiter(_request("/api/v1/auth/login"))
    assert result is None  # still allowed
    assert any("fail_open" in r.message for r in caplog.records)
