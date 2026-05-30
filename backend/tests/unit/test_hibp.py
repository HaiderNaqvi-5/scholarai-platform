import pytest
from unittest.mock import AsyncMock, patch
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
