"""Task 35: local JWT standardized on PyJWT with required-claims enforcement.

Covers:
1. Valid token round-trips (encode -> decode returns the claims).
2. A token missing a required claim (no "type") is rejected.
3. A tampered/invalid-signature token is rejected with the expected exception.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import create_access_token, decode_token
from scholarai_common.errors import ScholarAIException, ErrorCode


def test_valid_token_round_trips():
    token = create_access_token({"sub": "user-1", "role": "student"})
    payload = decode_token(token, expected_type="access")

    assert payload["sub"] == "user-1"
    assert payload["role"] == "student"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_token_missing_required_claim_is_rejected():
    # Build a token missing "sub" directly with PyJWT, bypassing
    # create_access_token. "type"/"exp" are present and correct so the
    # only way this gets rejected is the decode-time required-claims
    # enforcement (decode_token's own type-equality check would not catch
    # a missing "sub" on its own).
    bad_token = jwt.encode(
        {"type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    with pytest.raises(ScholarAIException) as caught:
        decode_token(bad_token, expected_type="access")

    assert caught.value.status_code == 401
    assert caught.value.code == ErrorCode.AUTH_TOKEN_EXPIRED


def test_tampered_token_is_rejected():
    token = create_access_token({"sub": "user-1", "role": "student"})
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(ScholarAIException) as caught:
        decode_token(tampered, expected_type="access")

    assert caught.value.status_code == 401
    assert caught.value.code == ErrorCode.AUTH_TOKEN_EXPIRED
