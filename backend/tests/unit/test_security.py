import pytest
from fastapi import HTTPException

from app.core.security import create_access_token, create_refresh_token, decode_token


def test_decode_token_accepts_matching_token_type():
    token = create_access_token({"sub": "user-1", "role": "student"})
    payload = decode_token(token, expected_type="access")

    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"


def test_decode_token_rejects_wrong_token_type():
    token = create_access_token({"sub": "user-1", "role": "student"})

    with pytest.raises(HTTPException) as caught:
        decode_token(token, expected_type="refresh")

    assert caught.value.status_code == 401
