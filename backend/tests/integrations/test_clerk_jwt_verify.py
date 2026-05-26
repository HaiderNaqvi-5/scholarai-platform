import time
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt as pyjwt

from app.integrations.clerk.jwt_verify import verify_clerk_jwt, ClerkClaims, ClerkAuthError


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


def test_valid_token_returns_claims(monkeypatch, rsa_keypair):
    priv, pub = rsa_keypair
    monkeypatch.setattr(
        "app.integrations.clerk.jwt_verify._get_jwks_keys",
        lambda: {"test-kid": pub},
    )
    token = _sign(priv, {
        "sub": "user_2abc", "iss": "https://example.clerk.accounts.dev",
        "exp": int(time.time()) + 60, "iat": int(time.time()),
        "azp": "https://app.grantpath.app",
    })
    claims = verify_clerk_jwt(token)
    assert isinstance(claims, ClerkClaims)
    assert claims.sub == "user_2abc"


def test_expired_token_raises(monkeypatch, rsa_keypair):
    priv, pub = rsa_keypair
    monkeypatch.setattr(
        "app.integrations.clerk.jwt_verify._get_jwks_keys",
        lambda: {"test-kid": pub},
    )
    token = _sign(priv, {
        "sub": "user_2abc", "exp": int(time.time()) - 10, "iat": int(time.time()) - 60,
    })
    with pytest.raises(ClerkAuthError, match="expired"):
        verify_clerk_jwt(token)


def test_unknown_kid_raises(monkeypatch, rsa_keypair):
    priv, _ = rsa_keypair
    monkeypatch.setattr("app.integrations.clerk.jwt_verify._get_jwks_keys", lambda: {})
    token = _sign(priv, {"sub": "x", "exp": int(time.time()) + 60})
    with pytest.raises(ClerkAuthError, match="unknown kid"):
        verify_clerk_jwt(token)


def test_alg_none_rejected():
    bad = pyjwt.encode({"sub": "x"}, key="", algorithm="none")
    with pytest.raises(ClerkAuthError):
        verify_clerk_jwt(bad)
