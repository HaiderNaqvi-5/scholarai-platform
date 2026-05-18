"""Unit tests for S8 account lockout (Redis-backed sliding window).

Uses a fakeredis stand-in via monkey-patching `_redis_client` so tests
run without a live Redis instance and stay deterministic.
"""

from __future__ import annotations

import pytest

from app.core import account_lockout


class _FakeRedis:
    """Minimal async Redis stub supporting incr/expire/get/set/delete +
    pipeline transactions."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value
        return True

    async def delete(self, *keys: str):
        n = 0
        for k in keys:
            if self.store.pop(k, None) is not None:
                n += 1
        return n

    def pipeline(self, *, transaction: bool = True):
        return _FakePipeline(self)


class _FakePipeline:
    def __init__(self, parent: _FakeRedis):
        self.parent = parent
        self.results: list = []

    async def incr(self, key: str):
        current = int(self.parent.store.get(key, "0")) + 1
        self.parent.store[key] = str(current)
        self.results.append(current)

    async def expire(self, key: str, seconds: int):
        # No real TTL — tests use clear() between cases.
        self.results.append(True)

    async def execute(self):
        out, self.results = self.results, []
        return out

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def fake_redis(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(account_lockout, "_redis_client", fake)
    return fake


@pytest.mark.asyncio
async def test_register_failure_does_not_lock_below_threshold(fake_redis, monkeypatch):
    monkeypatch.setattr(account_lockout.settings, "AUTH_LOCKOUT_MAX_FAILURES", 5)
    for _ in range(4):
        tripped = await account_lockout.register_failure("alice@example.com")
        assert tripped is False
    assert await account_lockout.is_locked("alice@example.com") is False


@pytest.mark.asyncio
async def test_register_failure_locks_at_threshold(fake_redis, monkeypatch):
    monkeypatch.setattr(account_lockout.settings, "AUTH_LOCKOUT_MAX_FAILURES", 3)
    for _ in range(2):
        await account_lockout.register_failure("bob@example.com")
    tripped = await account_lockout.register_failure("bob@example.com")
    assert tripped is True
    assert await account_lockout.is_locked("bob@example.com") is True


@pytest.mark.asyncio
async def test_email_normalization_case_insensitive(fake_redis, monkeypatch):
    monkeypatch.setattr(account_lockout.settings, "AUTH_LOCKOUT_MAX_FAILURES", 2)
    await account_lockout.register_failure("Carol@Example.COM")
    await account_lockout.register_failure("carol@example.com")
    assert await account_lockout.is_locked("CAROL@EXAMPLE.COM") is True


@pytest.mark.asyncio
async def test_clear_wipes_lock_and_failures(fake_redis, monkeypatch):
    monkeypatch.setattr(account_lockout.settings, "AUTH_LOCKOUT_MAX_FAILURES", 2)
    await account_lockout.register_failure("dave@example.com")
    await account_lockout.register_failure("dave@example.com")
    assert await account_lockout.is_locked("dave@example.com") is True
    await account_lockout.clear("dave@example.com")
    assert await account_lockout.is_locked("dave@example.com") is False


@pytest.mark.asyncio
async def test_redis_outage_fails_open(monkeypatch):
    import redis.asyncio as redis

    class _BrokenRedis:
        async def get(self, *_a, **_k):
            raise redis.RedisError("boom")

        async def delete(self, *_a, **_k):
            raise redis.RedisError("boom")

        def pipeline(self, *_, **__):
            raise redis.RedisError("boom")

    monkeypatch.setattr(account_lockout, "_redis_client", _BrokenRedis())
    # Lock check fails open (returns False, doesn't raise).
    assert await account_lockout.is_locked("oops@example.com") is False
    # Increment swallows error.
    assert await account_lockout.register_failure("oops@example.com") is False
    # Clear swallows error.
    await account_lockout.clear("oops@example.com")
