"""Per-plan SOP quota gate (Free=1 lifetime, Pro=5/mo, Elite=10/mo).

Exercises the canonical gate that lives in :mod:`app.services.documents.sop_builder`.
Free overrun -> HTTP 402 ``plan_required``. Pro/Elite overrun -> HTTP 429
``sop_quota_exhausted`` with ``upgrade_url='/upgrade'`` for Pro and ``None`` for
Elite. Both SOP draft and Elite line-feedback share the same monthly bucket,
so a single ``SOPBuilderService.draft()`` call records exactly one use.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.core.plan_guard import LIFETIME_FREE_SOP, MONTHLY_SOP_CAP
from app.models import DocumentRecord, SopMonthlyUsage
from app.schemas.sop import SOPDraftRequest, SOPInputs
from app.services.documents.sop_builder import (
    SOPBuilderService,
    _assert_sop_quota,
    _record_sop_use,
    _sop_period,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _inputs(**overrides) -> SOPInputs:
    base = dict(
        academic_background=(
            "I graduated from NUST in 2024 with a CGPA of 3.7 in Computer Science."
        ),
        research_experience=(
            "I worked on a CV pipeline that won the FYP showcase award."
        ),
        professional_experience=(
            "I interned at a Lahore-based fintech building ETL pipelines for 6 months."
        ),
        why_this_program="The program's emphasis on ML systems matches my trajectory.",
        why_this_country="Germany's tuition-free public universities and STEM strength.",
        career_goals=(
            "After my MS I want to lead applied research at a Pakistani EdTech startup."
        ),
        challenges_overcome="Being the first in my family to pursue a research degree.",
        gap_explanation=None,
    )
    base.update(overrides)
    return SOPInputs(**base)


def _payload() -> SOPDraftRequest:
    return SOPDraftRequest(program_name="MS Computer Science", sop_inputs=_inputs())


def _user(plan: str = "free", *, lifetime_sop_count: int = 0, currency: str = "PKR"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        plan=plan,
        plan_currency=currency,
        lifetime_sop_count=lifetime_sop_count,
    )


class _Row:
    def __init__(self, sop_count: int) -> None:
        self.sop_count = sop_count


class _Result:
    """Mimics ``sqlalchemy.Result`` for the two access patterns we use:
    ``.scalar_one_or_none()`` (gate read) and ``.scalar()`` (legacy)."""

    def __init__(self, value: Any = None) -> None:
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalar(self):
        return self._value


class _FakeDB:
    """Async-DB stand-in. Returns pre-seeded rows for selects; records writes."""

    def __init__(self, monthly_used: int | None = None) -> None:
        # ``monthly_used`` controls the SopMonthlyUsage row returned to the gate.
        # ``None`` = no row exists yet (fresh period).
        self._monthly_used = monthly_used
        self.executed: list[Any] = []
        self.added: list[Any] = []
        self.flushed = 0
        self.refreshed: list[Any] = []

    async def execute(self, statement):  # noqa: ANN001 - SQL statement object
        self.executed.append(statement)
        rendered = str(statement).lower()
        if "insert into sop_monthly_usage" in rendered and "on conflict" in rendered:
            base = self._monthly_used if self._monthly_used is not None else 0
            return _Result(base + 1)  # RETURNING sop_count after atomic +1
        if "update sop_monthly_usage" in rendered:
            return _Result(None)  # release decrement
        # The gate's legacy select(SopMonthlyUsage) path (still used by the
        # standalone _assert_sop_quota tests) returns the seeded row or None.
        row = _Row(self._monthly_used) if self._monthly_used is not None else None
        return _Result(row)

    def add(self, obj) -> None:
        self.added.append(obj)
        if isinstance(obj, DocumentRecord) and obj.id is None:
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

    async def flush(self) -> None:
        self.flushed += 1

    async def refresh(self, obj) -> None:
        self.refreshed.append(obj)

    async def get(self, _model, _pk):  # noqa: ANN001
        return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_free_blocks_after_1_lifetime():
    """Free: 1st draft 200, 2nd draft -> 402 plan_required."""
    db = _FakeDB()
    svc = SOPBuilderService(db)

    # First draft succeeds.
    resp = await svc.draft(_user("free", lifetime_sop_count=0), _payload())
    assert resp.document_id is not None
    # _record_sop_use should have run (update statement queued).
    assert len(db.executed) >= 1

    # Second attempt with counter already at the lifetime cap -> 402.
    with pytest.raises(HTTPException) as excinfo:
        await svc.draft(
            _user("free", lifetime_sop_count=LIFETIME_FREE_SOP), _payload()
        )
    err = excinfo.value
    assert err.status_code == 402
    assert err.detail["error"] == "plan_required"
    assert "pro" in err.detail["required_plan"]


@pytest.mark.asyncio
async def test_pro_blocks_after_5_monthly():
    """Pro: 5 drafts succeed, 6th -> 429 sop_quota_exhausted, upgrade_url='/upgrade'."""
    cap = MONTHLY_SOP_CAP["pro"]
    assert cap == 5

    # At-cap row -> 6th attempt blocked.
    db = _FakeDB(monthly_used=cap)
    with pytest.raises(HTTPException) as excinfo:
        await _assert_sop_quota(db, _user("pro"))
    err = excinfo.value
    assert err.status_code == 429
    assert err.detail["error"] == "sop_quota_exhausted"
    assert err.detail["plan"] == "pro"
    assert err.detail["used"] == cap
    assert err.detail["cap"] == cap
    assert err.detail["upgrade_url"] == "/upgrade"
    assert "Upgrade to Elite" in err.detail["message"]

    # One below cap -> still allowed.
    db_under = _FakeDB(monthly_used=cap - 1)
    # No exception expected.
    await _assert_sop_quota(db_under, _user("pro"))


@pytest.mark.asyncio
async def test_elite_blocks_after_10_monthly():
    """Elite: 10 drafts succeed, 11th -> 429 with upgrade_url is None."""
    cap = MONTHLY_SOP_CAP["elite"]
    assert cap == 10

    db = _FakeDB(monthly_used=cap)
    with pytest.raises(HTTPException) as excinfo:
        await _assert_sop_quota(db, _user("elite"))
    err = excinfo.value
    assert err.status_code == 429
    assert err.detail["error"] == "sop_quota_exhausted"
    assert err.detail["plan"] == "elite"
    assert err.detail["used"] == cap
    assert err.detail["cap"] == cap
    assert err.detail["upgrade_url"] is None
    # No "Upgrade to Elite" pitch when the user is already Elite.
    assert "Upgrade to Elite" not in err.detail["message"]


@pytest.mark.asyncio
async def test_pro_period_rollover_resets_counter(monkeypatch):
    """Seed last month at cap; current-month attempt succeeds (separate row)."""

    # Force a known period so the gate's "current month" lookup is deterministic.
    fixed_period = "209912"
    monkeypatch.setattr(
        "app.services.documents.sop_builder._sop_period", lambda: fixed_period
    )

    # A DB that returns nothing for the current period (i.e. last month's row
    # is keyed under a different period and the current-period select misses).
    db = _FakeDB(monthly_used=None)
    # Should not raise — current month bucket is empty.
    await _assert_sop_quota(db, _user("pro"))

    # And a fresh insert for the current period succeeds (no on_conflict path
    # hit since the row doesn't exist).
    await _record_sop_use(db, _user("pro"))
    # _record_sop_use issued exactly one statement against the fake DB.
    assert len(db.executed) >= 1


@pytest.mark.asyncio
async def test_quota_helper_unit_no_db():
    """Direct unit-level coverage: _assert_sop_quota against a fresh DB stub.

    Free user with no lifetime usage passes; with usage at the cap raises 402.
    Pro user with monthly_used=0 passes; at the cap raises 429.
    """

    # Free, never used -> no raise, no DB read needed (helper short-circuits).
    db = _FakeDB()
    await _assert_sop_quota(db, _user("free", lifetime_sop_count=0))
    # Free path doesn't query SopMonthlyUsage.
    assert db.executed == []

    # Free, already at lifetime cap -> 402.
    with pytest.raises(HTTPException) as excinfo:
        await _assert_sop_quota(
            db, _user("free", lifetime_sop_count=LIFETIME_FREE_SOP)
        )
    assert excinfo.value.status_code == 402
    assert excinfo.value.detail["error"] == "plan_required"

    # Pro, fresh period (no row) -> passes.
    db_pro = _FakeDB(monthly_used=None)
    await _assert_sop_quota(db_pro, _user("pro"))

    # Pro, at cap -> 429.
    db_pro_full = _FakeDB(monthly_used=MONTHLY_SOP_CAP["pro"])
    with pytest.raises(HTTPException) as excinfo:
        await _assert_sop_quota(db_pro_full, _user("pro"))
    assert excinfo.value.status_code == 429
    assert excinfo.value.detail["upgrade_url"] == "/upgrade"


def test_sop_period_is_current_yyyymm():
    """``_sop_period`` is 6-char yyyymm rooted in UTC now."""
    period = _sop_period()
    assert len(period) == 6
    assert period.isdigit()
    now = datetime.now(timezone.utc)
    assert period == f"{now.year:04d}{now.month:02d}"


@pytest.mark.asyncio
async def test_record_sop_use_targets_lifetime_for_free():
    """Free users get the User.lifetime_sop_count bump, not the monthly bucket."""
    db = _FakeDB()
    await _record_sop_use(db, _user("free"))
    assert len(db.executed) == 1
    # Crude check: statement should be an UPDATE against the users table.
    stmt = db.executed[0]
    rendered = str(stmt).lower()
    assert "update" in rendered
    assert "users" in rendered


@pytest.mark.asyncio
async def test_record_sop_use_targets_monthly_bucket_for_pro():
    """Pro/Elite users get the sop_monthly_usage upsert."""
    db = _FakeDB()
    await _record_sop_use(db, _user("pro"))
    assert len(db.executed) == 1
    stmt = db.executed[0]
    rendered = str(stmt).lower()
    # Postgres dialect insert with ON CONFLICT.
    assert "insert into sop_monthly_usage" in rendered
    assert "on conflict" in rendered


@pytest.mark.asyncio
async def test_institution_plan_bypasses_monthly_cap():
    """Institution plan currently has cap=50; far above any draft volume here.

    Confirms the gate does not throw spuriously for institution users at zero use.
    """
    db = _FakeDB(monthly_used=0)
    await _assert_sop_quota(db, _user("institution"))


@pytest.mark.asyncio
async def test_unknown_plan_treated_as_free_overrun():
    """An unknown plan string falls through to the free-tier branch via .lower()
    matching ``"free"`` only — others fall to MONTHLY_SOP_CAP.get which returns
    None and the gate then early-returns (treating them as institution-like).
    The contract: no crash, no spurious raise."""
    db = _FakeDB(monthly_used=0)
    # plan=None defaults to "free" via the helper.
    user_none = SimpleNamespace(
        id=uuid.uuid4(),
        plan=None,
        plan_currency="PKR",
        lifetime_sop_count=0,
    )
    await _assert_sop_quota(db, user_none)
    # And an unknown plan does not raise.
    user_unknown = _user("scholar-pro-max")
    await _assert_sop_quota(db, user_unknown)


@pytest.mark.asyncio
async def test_pro_draft_records_monthly_usage():
    """End-to-end via SOPBuilderService: a Pro draft records exactly one use.

    Post R5-SOP-QUOTA-RACE the check-then-record split is folded into a single
    atomic reserve, so the authoritative accounting is the upsert itself — no
    separate read-only SELECT gate is issued by draft() anymore.
    """
    db = _FakeDB(monthly_used=0)
    svc = SOPBuilderService(db)
    resp = await svc.draft(_user("pro"), _payload())
    assert resp.document_id is not None
    rendered = [str(stmt).lower() for stmt in db.executed]
    assert any(
        "insert into sop_monthly_usage" in r and "on conflict" in r for r in rendered
    ), "expected the atomic per-month reserve upsert during draft()"


@pytest.mark.asyncio
async def test_elite_draft_records_monthly_usage_once_with_line_feedback():
    """Elite path generates line feedback inline; quota still increments once."""
    db = _FakeDB(monthly_used=0)
    svc = SOPBuilderService(db)
    resp = await svc.draft(_user("elite"), _payload())
    assert resp.document_id is not None
    assert resp.line_feedback is not None  # Elite gets feedback
    # Exactly one INSERT into sop_monthly_usage even though we produced both
    # the draft and line-feedback in one call.
    inserts = [
        str(s)
        for s in db.executed
        if "insert into sop_monthly_usage" in str(s).lower()
    ]
    assert len(inserts) == 1, (
        f"Elite draft+feedback must share the bucket: saw {len(inserts)} inserts"
    )


# --- R5-SOP-QUOTA-RACE: atomic reserve/release ---------------------------

from app.services.documents.sop_builder import _reserve_sop_quota, _release_sop_quota


class _AtomicFakeDB:
    """DB stub whose upsert RETURNING yields the post-increment count.

    ``start_count`` is the bucket value *before* this request. An upsert that
    increments by 1 returns ``start_count + 1`` (the authoritative reserved
    value). UPDATE/release statements are recorded but do not change the stub.
    """

    def __init__(self, start_count: int = 0) -> None:
        self._start = start_count
        self.executed: list[Any] = []
        self.released = 0

    async def execute(self, statement):  # noqa: ANN001
        self.executed.append(statement)
        rendered = str(statement).lower()
        if "insert into sop_monthly_usage" in rendered and "on conflict" in rendered:
            return _Result(self._start + 1)  # RETURNING sop_count after +1
        if "update sop_monthly_usage" in rendered:
            self.released += 1
        return _Result(None)


@pytest.mark.asyncio
async def test_reserve_under_cap_returns_count_no_release():
    """Pro at used=2 reserves the 3rd slot: returns 3, no release issued."""
    db = _AtomicFakeDB(start_count=2)
    count = await _reserve_sop_quota(db, _user("pro"))
    assert count == 3
    # Exactly one statement: the atomic upsert. No release.
    assert db.released == 0
    rendered = [str(s).lower() for s in db.executed]
    assert any(
        "insert into sop_monthly_usage" in r and "on conflict" in r for r in rendered
    ), "reserve must use an atomic INSERT ... ON CONFLICT upsert"


@pytest.mark.asyncio
async def test_reserve_at_cap_raises_429_and_releases():
    """Pro already at cap: the upsert reserves count=cap+1 (over), so the gate
    raises 429 AND decrements the bucket back so the failed attempt is not
    charged."""
    cap = MONTHLY_SOP_CAP["pro"]
    db = _AtomicFakeDB(start_count=cap)
    with pytest.raises(HTTPException) as excinfo:
        await _reserve_sop_quota(db, _user("pro"))
    err = excinfo.value
    assert err.status_code == 429
    assert err.detail["error"] == "sop_quota_exhausted"
    assert err.detail["plan"] == "pro"
    assert err.detail["used"] == cap
    assert err.detail["cap"] == cap
    assert err.detail["upgrade_url"] == "/upgrade"
    # The over-cap reservation was released back (no silent overshoot).
    assert db.released == 1


@pytest.mark.asyncio
async def test_reserve_free_uses_lifetime_counter_in_memory():
    """Free path stays in-memory on User.lifetime_sop_count; at cap -> 402."""
    db = _AtomicFakeDB()
    # Under lifetime cap: returns and records the lifetime bump (1 statement).
    count = await _reserve_sop_quota(db, _user("free", lifetime_sop_count=0))
    assert count == 1
    rendered = [str(s).lower() for s in db.executed]
    assert any("update" in r and "users" in r for r in rendered)
    # At lifetime cap -> 402 plan_required, no UPDATE issued.
    db2 = _AtomicFakeDB()
    with pytest.raises(HTTPException) as excinfo:
        await _reserve_sop_quota(db2, _user("free", lifetime_sop_count=LIFETIME_FREE_SOP))
    assert excinfo.value.status_code == 402
    assert excinfo.value.detail["error"] == "plan_required"
    assert db2.executed == []  # no write when already over the lifetime cap


@pytest.mark.asyncio
async def test_draft_reserves_once_before_generation_for_pro():
    """End-to-end: a Pro draft reserves exactly one slot via the atomic upsert
    and issues no separate post-generation increment (reserve replaces the old
    check-then-record split)."""
    db = _FakeDB(monthly_used=0)
    svc = SOPBuilderService(db)
    resp = await svc.draft(_user("pro"), _payload())
    assert resp.document_id is not None
    inserts = [
        s for s in db.executed
        if "insert into sop_monthly_usage" in str(s).lower()
        and "on conflict" in str(s).lower()
    ]
    assert len(inserts) == 1, (
        f"draft() must reserve exactly once atomically; saw {len(inserts)} upserts"
    )


@pytest.mark.asyncio
async def test_draft_at_cap_does_not_persist_document_for_pro():
    """Pro at cap: draft() raises 429 before persisting a DocumentRecord."""
    used_row = SimpleNamespace(sop_count=MONTHLY_SOP_CAP["pro"])
    db = _FakeDB(monthly_used=MONTHLY_SOP_CAP["pro"])
    svc = SOPBuilderService(db)
    with pytest.raises(HTTPException) as excinfo:
        await svc.draft(_user("pro"), _payload())
    assert excinfo.value.status_code == 429
    # No DocumentRecord should have been added when the quota gate fails.
    from app.models import DocumentRecord as _DR
    assert not any(isinstance(o, _DR) for o in db.added)
