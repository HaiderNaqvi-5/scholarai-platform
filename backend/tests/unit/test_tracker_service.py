"""Unit tests for application tracker (Feature 6)."""

import uuid
from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.core.plan_guard import TRACKER_CAP
from app.models import default_document_checklist
from app.schemas.tracker import (
    TrackerChecklistPatchRequest,
    TrackerItemCreateRequest,
    TrackerStageUpdateRequest,
)
from app.services.tracker.service import FREE_PLAN_ITEM_LIMIT, TrackerService


class _FakeResult:
    def __init__(self, *, scalar: Any = None, scalars: list[Any] | None = None) -> None:
        self._scalar = scalar
        self._scalars = scalars or []

    def scalar(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        rows = self._scalars

        class _Scalars:
            def all(self_inner):
                return rows

        return _Scalars()


class _FakeDB:
    """Minimal stand-in for AsyncSession; queue results in order."""

    def __init__(self, *, results: list[_FakeResult] | None = None) -> None:
        self._results = list(results or [])
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.flushed = 0
        self.refreshed: list[Any] = []

    async def execute(self, _statement):
        if not self._results:
            return _FakeResult()
        return self._results.pop(0)

    def add(self, obj) -> None:
        self.added.append(obj)

    async def delete(self, obj) -> None:
        self.deleted.append(obj)

    async def flush(self) -> None:
        self.flushed += 1

    async def refresh(self, obj) -> None:
        self.refreshed.append(obj)

    async def get(self, _model, _pk):
        return None


def _user(plan: str = "free", currency: str = "PKR"):
    return SimpleNamespace(id=uuid.uuid4(), plan=plan, plan_currency=currency)


@pytest.mark.asyncio
async def test_default_document_checklist_includes_hec_attestation():
    checklist = default_document_checklist()
    assert "hec_attestation" in checklist
    assert checklist["hec_attestation"] is False


@pytest.mark.asyncio
async def test_create_succeeds_under_free_limit():
    user = _user("free")
    db = _FakeDB(results=[_FakeResult(scalar=0)])  # current count
    svc = TrackerService(db)
    item = await svc.create(
        user,
        TrackerItemCreateRequest(program_name="MS CS", country="GB", stage="researching"),
    )
    assert item.user_id == user.id
    assert item.stage == "researching"
    assert "hec_attestation" in item.document_checklist


@pytest.mark.asyncio
async def test_create_rejected_when_free_limit_reached():
    user = _user("free")
    db = _FakeDB(results=[_FakeResult(scalar=FREE_PLAN_ITEM_LIMIT), _FakeResult(scalar=7)])
    svc = TrackerService(db)
    with pytest.raises(HTTPException) as excinfo:
        await svc.create(user, TrackerItemCreateRequest(program_name="MS CS"))
    err = excinfo.value
    assert err.status_code == 402
    assert err.detail["error"] == "plan_limit_reached"
    assert err.detail["untracked_count"] == 7
    assert err.detail["current_items"] == FREE_PLAN_ITEM_LIMIT
    assert err.detail["cap"] == FREE_PLAN_ITEM_LIMIT


@pytest.mark.asyncio
async def test_pro_user_succeeds_when_under_cap():
    """Pro tier still has a cap (6) but should accept items below it."""
    user = _user("pro")
    db = _FakeDB(results=[_FakeResult(scalar=0)])
    svc = TrackerService(db)
    item = await svc.create(user, TrackerItemCreateRequest(program_name="MS CS"))
    assert item.user_id == user.id


@pytest.mark.parametrize(
    "plan,cap",
    [
        ("free", TRACKER_CAP["free"]),
        ("pro", TRACKER_CAP["pro"]),
        ("elite", TRACKER_CAP["elite"]),
    ],
)
@pytest.mark.asyncio
async def test_tracker_cap_per_plan_blocks_over_cap(plan, cap):
    """At-cap creates raise 402 plan_required for every paid tier below institution."""
    user = _user(plan)
    # First execute() inside create() returns the count; second returns the
    # untracked-upcoming-deadlines count used to enrich the upgrade prompt.
    db = _FakeDB(results=[_FakeResult(scalar=cap), _FakeResult(scalar=4)])
    svc = TrackerService(db)
    with pytest.raises(HTTPException) as excinfo:
        await svc.create(user, TrackerItemCreateRequest(program_name="MS CS"))
    err = excinfo.value
    assert err.status_code == 402
    assert err.detail["error"] == "plan_limit_reached"
    assert err.detail["cap"] == cap
    assert err.detail["current_items"] == cap


@pytest.mark.parametrize(
    "plan,cap",
    [
        ("free", TRACKER_CAP["free"]),
        ("pro", TRACKER_CAP["pro"]),
        ("elite", TRACKER_CAP["elite"]),
    ],
)
@pytest.mark.asyncio
async def test_tracker_cap_per_plan_allows_under_cap(plan, cap):
    """Just-below-cap creates succeed for every paid tier."""
    user = _user(plan)
    db = _FakeDB(results=[_FakeResult(scalar=cap - 1)])
    svc = TrackerService(db)
    item = await svc.create(user, TrackerItemCreateRequest(program_name="MS CS"))
    assert item.user_id == user.id


@pytest.mark.asyncio
async def test_institution_cap_blocks_at_fifty():
    """Institution sits at the top of the ladder but the gate still fires."""
    user = _user("institution")
    db = _FakeDB(
        results=[
            _FakeResult(scalar=TRACKER_CAP["institution"]),
            _FakeResult(scalar=0),
        ]
    )
    svc = TrackerService(db)
    with pytest.raises(HTTPException) as excinfo:
        await svc.create(user, TrackerItemCreateRequest(program_name="MS CS"))
    err = excinfo.value
    assert err.status_code == 402
    assert err.detail["cap"] == TRACKER_CAP["institution"]


def test_stage_update_request_rejects_unknown_stage():
    with pytest.raises(Exception):
        TrackerStageUpdateRequest(stage="rejected_stage")


def test_stage_update_request_normalises_case():
    payload = TrackerStageUpdateRequest(stage="APPLIED")
    assert payload.stage == "applied"


def test_checklist_patch_rejects_unknown_keys():
    with pytest.raises(Exception):
        TrackerChecklistPatchRequest(checklist={"unknown_doc": True})


def test_checklist_patch_accepts_known_keys():
    payload = TrackerChecklistPatchRequest(
        checklist={"sop_final": True, "hec_attestation": True}
    )
    assert payload.checklist["hec_attestation"] is True


def test_tracker_create_default_stage_is_researching():
    payload = TrackerItemCreateRequest(program_name="MS")
    assert payload.stage == "researching"


def test_tracker_create_uppercases_country():
    payload = TrackerItemCreateRequest(program_name="MS", country="de")
    assert payload.country == "DE"


def test_tracker_create_deadline_field_accepts_date():
    payload = TrackerItemCreateRequest(
        program_name="MS",
        deadline=date(2026, 11, 5),
    )
    assert payload.deadline.year == 2026
