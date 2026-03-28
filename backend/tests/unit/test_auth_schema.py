import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreate


def test_user_create_accepts_strong_password():
    payload = UserCreate(
        email="user@example.com",
        password="StrongPass123!",
        full_name="Test User",
    )
    assert payload.password == "StrongPass123!"


@pytest.mark.parametrize(
    "password,expected",
    [
        ("short1A!", "at least 12"),
        ("alllowercase123!", "uppercase"),
        ("ALLUPPERCASE123!", "lowercase"),
        ("NoDigitsOnly!!!", "number"),
        ("NoSpecials1234", "special character"),
    ],
)
def test_user_create_rejects_weak_passwords(password: str, expected: str):
    with pytest.raises(ValidationError) as caught:
        UserCreate(
            email="user@example.com",
            password=password,
            full_name="Test User",
        )
    assert expected in str(caught.value)
