"""P2-16: waitlist hardening — rate limit, extra="forbid", race-free upsert.

Offline (no Postgres needed): extra-field rejection (422, pure Pydantic
validation, DB never touched — proven with a tripwire DB) and rate-limit
tripping (fake async redis monkeypatched onto app.core.rate_limit, mirrors
the harness style of tests/unit/test_rate_limit.py). Both tests patch a fake
redis client so they never depend on a real Redis being reachable.

Postgres-gated (@requires_db, skip when TEST_DATABASE_URL unset): duplicate
POST /waitlist for the same email must not 500 (no IntegrityError from the
old select-then-insert race) and must not create a second row.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

import app.core.rate_limit as rate_limit
from app.core.database import get_db
from app.models import Waitlist

from tests.conftest import requires_db


class _FakeRedis:
    """Honest fixed-window emulation matching the limiter's INCR+NX-expire
    Lua contract (same shape as tests/unit/test_rate_limit.py's fake)."""

    def __init__(self):
        self.counts: dict[str, int] = {}

    async def eval(self, _script, _numkeys, key, window):  # noqa: ANN001
        new = self.counts.get(key, 0) + 1
        self.counts[key] = new
        return new


class _TripwireDB:
    """Records whether the route ever reached the DB layer. Used to prove
    request-body validation (extra="forbid") rejects before any DB call."""

    def __init__(self):
        self.executed = False

    async def execute(self, _stmt):
        self.executed = True
        raise AssertionError("DB should not be reached for a 422 rejection")

    async def commit(self):
        self.executed = True


class _StubResult:
    def __init__(self, row):
        self._row = row

    def one(self):
        return self._row


class _StubDB:
    """Mimics the ON CONFLICT ... RETURNING upsert without a real DB, so the
    rate-limit test can exercise real (non-rate-limited) requests all the
    way through the handler."""

    async def execute(self, _stmt):
        row = SimpleNamespace(
            id=uuid4(),
            email="stub@example.com",
            plan="pro",
            currency="PKR",
            country="PK",
            created_at=datetime.now(timezone.utc),
        )
        return _StubResult(row)

    async def commit(self):
        return None


def _payload(email: str = "waitlist-test@example.com") -> dict:
    return {"email": email, "plan": "pro", "currency": "PKR", "country": "PK"}


def test_extra_field_rejected_before_hitting_db(app, monkeypatch):
    """extra="forbid" on WaitlistJoinRequest -> 422, DB never reached."""
    monkeypatch.setattr(rate_limit, "redis_client", _FakeRedis())

    db = _TripwireDB()

    async def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    body = _payload()
    body["not_a_real_field"] = "sneaky"

    response = client.post("/api/v1/waitlist", json=body)

    assert response.status_code == 422
    assert db.executed is False


def test_rate_limit_trips_after_configured_requests(app, monkeypatch):
    """IP rate limiter caps POST /waitlist; the (limit+1)th call is 429."""
    monkeypatch.setattr(rate_limit, "redis_client", _FakeRedis())

    async def _override_db():
        yield _StubDB()

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)

    from app.api.v1.routes.waitlist import _WAITLIST_RATE_LIMIT

    limit = _WAITLIST_RATE_LIMIT.requests_limit
    statuses = []
    for i in range(limit + 1):
        resp = client.post("/api/v1/waitlist", json=_payload(email=f"rl-{i}@example.com"))
        statuses.append(resp.status_code)

    # Every request up to the limit reaches the (stubbed) handler and
    # succeeds; the (limit+1)th is rejected by the limiter dependency
    # before the handler runs at all.
    assert statuses[:limit] == [201] * limit
    assert statuses[-1] == 429


@requires_db
@pytest.mark.asyncio
async def test_duplicate_join_upserts_without_500(app_client, db_session):
    """Two POSTs for the same email: no IntegrityError 500, exactly one row."""
    email = f"dup-{uuid4()}@example.com"
    body = _payload(email=email)

    first = await app_client.post("/api/v1/waitlist", json=body)
    assert first.status_code == 201

    body["plan"] = "elite"
    second = await app_client.post("/api/v1/waitlist", json=body)
    assert second.status_code == 201
    assert second.json()["plan"] == "elite"

    count = await db_session.execute(
        select(func.count()).select_from(Waitlist).where(Waitlist.email == email)
    )
    assert count.scalar_one() == 1
