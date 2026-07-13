import inspect
import time
from unittest.mock import AsyncMock

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt as pyjwt

from app.integrations.clerk.jwt_verify import (
    _get_jwks_keys,
    verify_clerk_jwt,
    ClerkClaims,
    ClerkAuthError,
)


# ---------------------------------------------------------------------------
# Coroutine-function assertions (P2-2 structural guarantee)
# ---------------------------------------------------------------------------

def test_get_jwks_keys_is_coroutine_function():
    assert inspect.iscoroutinefunction(_get_jwks_keys)


def test_verify_clerk_jwt_is_coroutine_function():
    assert inspect.iscoroutinefunction(verify_clerk_jwt)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def rsa_keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


def _sign(priv, claims):
    return pyjwt.encode(claims, priv, algorithm="RS256", headers={"kid": "test-kid"})


# ---------------------------------------------------------------------------
# verify_clerk_jwt tests — patch the whole _get_jwks_keys coroutine so the
# tests exercise verify_clerk_jwt end-to-end without real httpx traffic.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_valid_token_returns_claims(monkeypatch, rsa_keypair):
    priv, pub = rsa_keypair
    monkeypatch.setattr(
        "app.integrations.clerk.jwt_verify._get_jwks_keys",
        AsyncMock(return_value={"test-kid": pub}),
    )
    token = _sign(priv, {
        "sub": "user_2abc", "iss": "https://example.clerk.accounts.dev",
        "exp": int(time.time()) + 60, "iat": int(time.time()),
        "azp": "https://app.grantpath.app",
    })
    claims = await verify_clerk_jwt(token)
    assert isinstance(claims, ClerkClaims)
    assert claims.sub == "user_2abc"


@pytest.mark.asyncio
async def test_expired_token_raises(monkeypatch, rsa_keypair):
    priv, pub = rsa_keypair
    monkeypatch.setattr(
        "app.integrations.clerk.jwt_verify._get_jwks_keys",
        AsyncMock(return_value={"test-kid": pub}),
    )
    token = _sign(priv, {
        "sub": "user_2abc", "exp": int(time.time()) - 10, "iat": int(time.time()) - 60,
    })
    with pytest.raises(ClerkAuthError, match="expired"):
        await verify_clerk_jwt(token)


@pytest.mark.asyncio
async def test_unknown_kid_raises(monkeypatch, rsa_keypair):
    priv, _ = rsa_keypair
    monkeypatch.setattr(
        "app.integrations.clerk.jwt_verify._get_jwks_keys",
        AsyncMock(return_value={}),
    )
    token = _sign(priv, {"sub": "x", "exp": int(time.time()) + 60})
    with pytest.raises(ClerkAuthError, match="unknown kid"):
        await verify_clerk_jwt(token)


@pytest.mark.asyncio
async def test_alg_none_rejected():
    bad = pyjwt.encode({"sub": "x"}, key="", algorithm="none")
    with pytest.raises(ClerkAuthError):
        await verify_clerk_jwt(bad)
