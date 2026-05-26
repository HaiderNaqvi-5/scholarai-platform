"""
Task 9: Legacy auth endpoints return 410 Gone when AUTH_PROVIDER=clerk.

The app uses ErrorEnvelope middleware — HTTPException.detail (str) maps to
response body: {"error": {"message": <detail>, "code": ..., ...}}.
So we check r.json()["error"]["message"] for the "clerk" substring.

/me is intentionally NOT gated (needed in clerk mode for the protected-route
test in test_clerk_protected_route.py).
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


@pytest.mark.parametrize("path,method", [
    ("/api/v1/auth/register", "post"),
    ("/api/v1/auth/login", "post"),
    ("/api/v1/auth/refresh", "post"),
    ("/api/v1/auth/logout", "post"),
])
def test_legacy_auth_returns_410_in_clerk_mode(monkeypatch, path, method):
    monkeypatch.setattr(settings, "AUTH_PROVIDER", "clerk")
    from app.main import app
    client = TestClient(app)
    r = getattr(client, method)(path, json={})
    assert r.status_code == 410
    assert "clerk" in r.json()["error"]["message"].lower()
