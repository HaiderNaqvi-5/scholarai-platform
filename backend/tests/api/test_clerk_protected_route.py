"""
Task 5: Dual-mode get_current_user tests (local | clerk).

Route under test: GET /api/v1/auth/me  (uses SessionReadUser which requires
Capability.AUTH_SESSION_READ).  In clerk mode, _get_user_from_clerk_jwt sets
_token_capabilities from role-based defaults so the capability guard passes
for any non-UNIVERSITY role that has AUTH_SESSION_READ.

Design choices / deviations from plan:
- The test mock's `role` is a real `UserRole.STUDENT` enum value (not a bare
  MagicMock) so that `get_role_capabilities` fallback works correctly.
- The mock user also has `_token_capabilities` set by `_get_user_from_clerk_jwt`
  via `get_role_capabilities(user.role)`, so the capability check passes.
- `ensure_local_user_async` is monkeypatched after import so the function
  attribute exists at the time of patching.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import UserRole


@pytest.fixture
def clerk_client_app(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_PROVIDER", "clerk")
    from app.main import create_app
    app = create_app()
    return TestClient(app)


def test_protected_route_rejects_local_jwt_in_clerk_mode(clerk_client_app):
    """Any token that fails verify_clerk_jwt should yield 401 in clerk mode."""
    r = clerk_client_app.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-clerk-token"},
    )
    assert r.status_code == 401


def test_protected_route_accepts_clerk_jwt(clerk_client_app, monkeypatch):
    """A token accepted by verify_clerk_jwt + a live user → 200."""
    from app.integrations.clerk import jwt_verify, user_sync

    fake_claims = MagicMock()
    fake_claims.sub = "user_clerk_test_001"

    # Build a realistic mock user so UserResponse serialisation succeeds.
    fake_user = MagicMock()
    fake_user.id = uuid.uuid4()
    fake_user.email = "x@x.com"
    fake_user.is_active = True
    fake_user.role = UserRole.STUDENT
    fake_user.full_name = "Test User"
    fake_user.clerk_user_id = "user_clerk_test_001"
    # Fields referenced by UserResponse schema (set safe defaults so Pydantic
    # serialisation succeeds — every str field must be a real str, not MagicMock).
    fake_user.plan = "free"
    fake_user.plan_currency = "PKR"
    fake_user.plan_country = "PK"
    fake_user.plan_expires_at = None
    fake_user.created_at = None
    fake_user.updated_at = None
    fake_user.institution_id = None
    fake_user.auth_token_version = 1
    fake_user.billing_country = None
    fake_user.air_uni_uni = None
    fake_user.air_uni_dept = None
    fake_user.redeemed_invite_code = None

    monkeypatch.setattr(jwt_verify, "verify_clerk_jwt", AsyncMock(return_value=fake_claims))
    monkeypatch.setattr(
        user_sync,
        "ensure_local_user_async",
        AsyncMock(return_value=fake_user),
    )

    r = clerk_client_app.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer fake.clerk.jwt"},
    )
    assert r.status_code == 200
