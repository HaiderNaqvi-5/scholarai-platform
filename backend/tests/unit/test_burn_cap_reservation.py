"""Unit tests for R10 burn-cap atomic reservation (Redis-backed).

Mirrors the fakeredis monkeypatch seam in tests/unit/test_account_lockout.py
so the tests run without a live Redis and stay deterministic offline.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core import burn_cap


class _FakeRedis:
    """Minimal async Redis stub: get / set / delete / incrby / decrby / expire."""

    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    async def get(self, key: str):
        val = self.store.get(key)
        return None if val is None else str(val)

    async def set(self, key: str, value, ex: int | None = None):
        self.store[key] = int(value)
        return True

    async def delete(self, *keys: str):
        n = 0
        for k in keys:
            if self.store.pop(k, None) is not None:
                n += 1
        return n

    async def incrby(self, key: str, amount: int):
        self.store[key] = self.store.get(key, 0) + int(amount)
        return self.store[key]

    async def decrby(self, key: str, amount: int):
        self.store[key] = self.store.get(key, 0) - int(amount)
        return self.store[key]

    async def expire(self, key: str, seconds: int):
        return True


class _ZeroLedgerResult:
    """SUM(cost_pkr_micro) == 0 -> nothing spent in the DB yet."""

    def scalar_one(self) -> int:
        return 0


class _FakeDB:
    async def execute(self, _statement):
        return _ZeroLedgerResult()


def _user(plan: str = "free"):
    # Free budget is PKR 50 (TIER_BUDGET_PKR["free"]).
    return SimpleNamespace(id="user-1", plan=plan, plan_currency="PKR")


@pytest.fixture
def fake_redis(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(burn_cap, "_redis_client", fake)
    return fake


async def test_reserve_burn_increments_atomically(fake_redis):
    user = _user("free")
    after = await burn_cap.reserve_burn(user, Decimal("10"))
    # 10 PKR reserved -> 10 * 1e6 micro-PKR held against the (user, period) key.
    assert after == int(Decimal("10") * burn_cap._MICRO)
    after2 = await burn_cap.reserve_burn(user, Decimal("5"))
    assert after2 == int(Decimal("15") * burn_cap._MICRO)


async def test_assert_counts_live_reservation_and_blocks_concurrent_overshoot(fake_redis):
    db = _FakeDB()
    user = _user("free")  # budget = PKR 50
    # First in-flight call has already reserved PKR 45.
    await burn_cap.reserve_burn(user, Decimal("45"))
    # A concurrent second call projecting PKR 10 would push 45 + 10 = 55 > 50.
    # The DB SUM is still 0 (neither call has written its ledger row yet), but
    # the reservation makes assert_within_burn_cap see the in-flight spend.
    with pytest.raises(burn_cap.HTTPException) as excinfo:
        await burn_cap.assert_within_burn_cap(db, user, Decimal("10"))
    assert excinfo.value.status_code == 429
    assert excinfo.value.detail["error"] == "burn_cap_reached"


async def test_assert_allows_when_reservation_fits(fake_redis):
    db = _FakeDB()
    user = _user("free")  # budget = PKR 50
    await burn_cap.reserve_burn(user, Decimal("20"))
    # 20 reserved + 20 projected = 40 <= 50 -> no raise.
    await burn_cap.assert_within_burn_cap(db, user, Decimal("20"))


async def test_release_reservation_decrements(fake_redis):
    user = _user("free")
    await burn_cap.reserve_burn(user, Decimal("30"))
    await burn_cap.release_reservation(user, Decimal("30"))
    key = burn_cap._RESERVE_KEY.format(user_id=user.id, period=burn_cap._period())
    assert int(fake_redis.store.get(key, 0)) == 0


async def test_redis_outage_fails_open(monkeypatch):
    import redis.asyncio as redis

    class _BrokenRedis:
        async def get(self, *_a, **_k):
            raise redis.RedisError("boom")

        async def incrby(self, *_a, **_k):
            raise redis.RedisError("boom")

        async def decrby(self, *_a, **_k):
            raise redis.RedisError("boom")

        async def expire(self, *_a, **_k):
            raise redis.RedisError("boom")

    monkeypatch.setattr(burn_cap, "_redis_client", _BrokenRedis())
    db = _FakeDB()
    user = _user("free")
    # Reservation no-ops (returns 0), release no-ops, and the cap check still
    # works off the DB SUM alone -> no raise, no crash.
    assert await burn_cap.reserve_burn(user, Decimal("10")) == 0
    await burn_cap.release_reservation(user, Decimal("10"))
    await burn_cap.assert_within_burn_cap(db, user, Decimal("5"))
