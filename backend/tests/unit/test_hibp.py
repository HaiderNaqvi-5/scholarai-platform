import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.hibp import is_pwned


@pytest.mark.asyncio
async def test_pwned_returns_true_when_suffix_in_response():
    # SHA1("password") = 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
    # prefix=5BAA6 ; suffix=1E4C9B93F3F0682250B6CF8331B7EE68FD8
    body = b"1E4C9B93F3F0682250B6CF8331B7EE68FD8:1234\r\nABCDE:1\r\n"
    with patch("app.core.hibp._fetch_range", AsyncMock(return_value=body)):
        assert await is_pwned("password") is True


@pytest.mark.asyncio
async def test_not_pwned_when_suffix_absent():
    with patch("app.core.hibp._fetch_range", AsyncMock(return_value=b"ZZZZZ:1\r\n")):
        assert await is_pwned("password") is False


@pytest.mark.asyncio
async def test_fail_open_on_network_error():
    with patch("app.core.hibp._fetch_range", AsyncMock(side_effect=TimeoutError())):
        assert await is_pwned("password") is False


# --- register() wiring (gated by settings.HIBP_BREACH_CHECK_ENABLED) ---

from app.core.config import settings
from app.services.auth.service import AuthService
from app.schemas import UserCreate
from scholarai_common.errors import ScholarAIException

_VALID = dict(email="new@example.com", password="Breached-Pass-123!", full_name="New User")


@pytest.mark.asyncio
async def test_register_rejects_pwned_password_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "HIBP_BREACH_CHECK_ENABLED", True)
    svc = AuthService(db=AsyncMock())
    with patch("app.services.auth.service.is_pwned", AsyncMock(return_value=True)):
        with pytest.raises(ScholarAIException) as ei:
            await svc.register(UserCreate(**_VALID))
    assert ei.value.status_code == 400
    svc.db.execute.assert_not_called()  # fail-fast before any DB work


@pytest.mark.asyncio
async def test_register_skips_breach_check_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "HIBP_BREACH_CHECK_ENABLED", False)
    checker = AsyncMock(return_value=True)
    svc = AuthService(db=AsyncMock())
    # existing-email select returns a truthy row → register short-circuits.
    svc.db.execute = AsyncMock(return_value=MagicMock())
    with patch("app.services.auth.service.is_pwned", checker):
        # Disabled → breach check skipped; existing-email select returns a
        # truthy mock so register short-circuits to None (email "exists").
        result = await svc.register(UserCreate(**_VALID))
    checker.assert_not_called()
    assert result is None
