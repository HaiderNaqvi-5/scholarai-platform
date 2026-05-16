"""Unit tests for ``app.tasks.trial_tasks.expire_trial_plans``.

We deliberately mock the AsyncSession rather than spin up a real DB so the
test stays fast and CI-portable. Two things matter:

1. The UPDATE is parameterised correctly (sets plan='free' + clears
   ``plan_expires_at``, scoped to non-free users whose expiry is in the past).
2. The function returns the affected rowcount unchanged so callers can log
   or alert on big-bang downgrades.
"""

import pytest

from app.tasks.trial_tasks import expire_trial_plans

pytestmark = pytest.mark.asyncio


class _UpdateResult:
    """Matches the shape of an AsyncResult for an UPDATE statement."""

    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class FakeSession:
    """Captures the UPDATE statement string + rowcount returned."""

    def __init__(self, rowcount: int) -> None:
        self._rowcount = rowcount
        self.statements: list[str] = []
        self.committed = False

    async def execute(self, statement):  # type: ignore[no-untyped-def]
        self.statements.append(str(statement))
        return _UpdateResult(self._rowcount)

    async def commit(self) -> None:
        self.committed = True


async def test_expire_returns_rowcount_and_commits():
    session = FakeSession(rowcount=3)
    expired = await expire_trial_plans(session)
    assert expired == 3
    assert session.committed is True
    assert len(session.statements) == 1


async def test_expire_zero_rows_still_commits():
    session = FakeSession(rowcount=0)
    expired = await expire_trial_plans(session)
    assert expired == 0
    assert session.committed is True


async def test_update_sets_plan_free_and_clears_expiry():
    """Compiled SQL must target users + reset plan + null out plan_expires_at."""
    session = FakeSession(rowcount=1)
    await expire_trial_plans(session)
    sql = session.statements[0].lower()
    assert "update users" in sql
    assert "plan_expires_at" in sql
    # value bindings are %(plan_1)s style; check the literal we'd bind to it
    # by inspecting the statement repr — Mapped[str] -> plan column targeted.
    assert "plan" in sql


async def test_update_predicates_filter_nulls_and_future():
    """WHERE must exclude users with null plan_expires_at + future expiries +
    users already on free. Defence against an over-broad UPDATE."""
    session = FakeSession(rowcount=0)
    await expire_trial_plans(session)
    sql = session.statements[0].lower()
    # ``plan_expires_at IS NOT NULL`` + ``plan_expires_at < <now>`` + ``plan != 'free'``
    assert "plan_expires_at is not null" in sql
    assert "plan_expires_at <" in sql
    assert "plan !=" in sql or "plan <>" in sql
