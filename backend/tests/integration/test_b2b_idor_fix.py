"""P1-2 IDOR fix: POST /b2b/share must reject cross-institution sharing.

These tests exercise the route handler directly via FastAPI's TestClient with
dependency overrides (fake DB + fake current_user) so they run offline without
Postgres.  Every branch of the new institution-scope check is covered.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_INST_A = uuid.uuid4()
_INST_B = uuid.uuid4()

_UNIVERSITY_ID = uuid.uuid4()
_TARGET_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# Minimal fake DB used by the IDOR tests.
# The route calls db.get(User, target_user_id) to fetch the target.
# B2BShareService is NOT reached for the negative / null-institution cases.
# For the positive case we stub out just enough for share_profile to succeed.
# ---------------------------------------------------------------------------


class _FakeDB:
    """Returns a pre-configured target User from db.get(User, …).

    B2BShareService also calls db.get(Institution, institution_id).
    We return the target_user for the User lookup and a stub institution
    (with dpa_signed_at=None) for any other model — that triggers the
    service-level DPA gate rather than an AttributeError.
    For the IDOR-negative cases the service is never reached.
    """

    def __init__(self, *, target_user: object | None):
        self._target = target_user

    async def get(self, model, _pk):
        from app.models import User as _User
        if model is _User:
            return self._target
        # Institution lookup inside B2BShareService — return stub with no DPA
        from types import SimpleNamespace as _SN
        return _SN(dpa_signed_at=None)

    # B2BShareService internals (consent check via execute()):
    async def execute(self, _stmt):
        return _FakeExecuteResult()

    def add(self, obj) -> None:
        import uuid as _uuid
        from datetime import datetime, timezone
        if not getattr(obj, "id", None):
            obj.id = _uuid.uuid4()
        if not getattr(obj, "shared_at", None):
            obj.shared_at = datetime.now(timezone.utc)

    async def flush(self) -> None:
        pass

    async def refresh(self, _obj) -> None:
        pass


class _FakeExecuteResult:
    def scalar_one_or_none(self):
        return None  # no consent row → service raises b2b_share_consent_missing


# ---------------------------------------------------------------------------
# Helper: build a caller SimpleNamespace that passes has_plan_at_least("institution")
# ---------------------------------------------------------------------------


def _caller(institution_id: uuid.UUID | None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        full_name="Caller User",
        email="caller@instA.edu.pk",
        role=UserRole.STUDENT,
        plan="institution",
        is_active=True,
        institution_id=institution_id,
        _token_capabilities=set(),
    )


def _target(institution_id: uuid.UUID | None) -> SimpleNamespace:
    return SimpleNamespace(
        id=_TARGET_ID,
        full_name="Target Student",
        email="student@example.com",
        plan="free",
        institution_id=institution_id,
        b2b_share_consent=True,
    )


# ---------------------------------------------------------------------------
# Payload
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {
    "target_user_id": str(_TARGET_ID),
    "university_id": str(_UNIVERSITY_ID),
    "institution_id": str(_INST_A),
    "share_reason": "match",
    "shared_with_email": None,
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_idor_cross_institution_share_returns_403(app, client):
    """IDOR negative: caller institution=A, target institution=B → 403."""
    caller = _caller(_INST_A)
    target_user = _target(_INST_B)  # different institution

    async def _user():
        return caller

    async def _db():
        yield _FakeDB(target_user=target_user)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = _db
    try:
        resp = client.post(
            "/api/v1/b2b/share",
            json=_VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403, resp.text
    body = resp.json()
    # App wraps HTTPException.detail in ErrorEnvelope: {"error": {"details": <original dict>}}
    details = body.get("error", {}).get("details", {})
    assert details.get("error") == "cross_institution_share_forbidden"


def test_idor_null_caller_institution_returns_403(app, client):
    """Caller with null institution_id (e.g. owner/platform account) → 403.

    Such accounts pass the plan gate but must not share into any institution.
    """
    caller = _caller(None)  # no institution affiliation
    target_user = _target(_INST_A)

    async def _user():
        return caller

    async def _db():
        yield _FakeDB(target_user=target_user)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = _db
    try:
        resp = client.post(
            "/api/v1/b2b/share",
            json=_VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403, resp.text
    body = resp.json()
    details = body.get("error", {}).get("details", {})
    assert details.get("error") == "cross_institution_share_forbidden"


def test_idor_same_institution_reaches_service(app, client):
    """Positive: caller and target are in the same institution.

    The institution-scope check passes and the request proceeds into
    B2BShareService. The service itself raises 403 because the fake DB returns
    no consent row (b2b_share_consent_missing).  That is the *service* gate,
    not the IDOR gate — proof that the IDOR check was cleared.
    """
    caller = _caller(_INST_A)
    target_user = _target(_INST_A)  # same institution

    async def _user():
        return caller

    async def _db():
        yield _FakeDB(target_user=target_user)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = _db
    try:
        resp = client.post(
            "/api/v1/b2b/share",
            json=_VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )
    finally:
        app.dependency_overrides.clear()

    # The IDOR gate passed. Service fires its own service-level gate → 403 with a
    # DIFFERENT error code proving we are past the IDOR check.
    # Target has b2b_share_consent=True so the consent gate passes; the fake DB
    # returns an Institution with dpa_signed_at=None → DPA gate fires next.
    assert resp.status_code == 403, resp.text
    body = resp.json()
    details = body.get("error", {}).get("details", {})
    # Must NOT be the IDOR error — we passed the institution-scope check
    assert details.get("error") != "cross_institution_share_forbidden"
    # Must be a service-level gate error (DPA not signed)
    assert details.get("error") == "institution_dpa_missing"


def test_idor_target_not_found_returns_404(app, client):
    """Non-existent target_user_id → 404 (IDOR check is after 404 guard)."""
    caller = _caller(_INST_A)

    async def _user():
        return caller

    async def _db():
        yield _FakeDB(target_user=None)  # db.get returns None

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = _db
    try:
        resp = client.post(
            "/api/v1/b2b/share",
            json=_VALID_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404, resp.text
