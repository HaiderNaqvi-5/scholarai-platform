from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
import jwt as pyjwt
from cryptography.hazmat.primitives import serialization
from jwt.algorithms import RSAAlgorithm

from app.core.config import settings


class ClerkAuthError(Exception):
    """Clerk token rejection."""


@dataclass(frozen=True, slots=True)
class ClerkClaims:
    sub: str
    iss: str | None
    azp: str | None
    exp: int
    iat: int
    raw: dict[str, Any]


_JWKS_TTL_SECONDS = 600
_jwks_cache: dict[str, Any] = {"keys": {}, "fetched_at": 0.0}


def _get_jwks_keys() -> dict[str, bytes]:
    now = time.time()
    if now - _jwks_cache["fetched_at"] < _JWKS_TTL_SECONDS and _jwks_cache["keys"]:
        return _jwks_cache["keys"]
    url = settings.CLERK_JWKS_URL
    if not url:
        raise ClerkAuthError("CLERK_JWKS_URL not configured")
    # Map JWKS-endpoint failures (timeout, DNS, TLS, 5xx) to ClerkAuthError so
    # they surface as 401, not a raw 500 across the whole authenticated surface.
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise ClerkAuthError(f"JWKS fetch failed: {e}") from e
    keys: dict[str, bytes] = {}
    for jwk in resp.json().get("keys", []):
        kid = jwk.get("kid")
        if not kid:
            continue
        public_key = RSAAlgorithm.from_jwk(jwk)
        keys[kid] = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    return keys


def verify_clerk_jwt(token: str) -> ClerkClaims:
    try:
        header = pyjwt.get_unverified_header(token)
    except pyjwt.DecodeError as e:
        raise ClerkAuthError(f"malformed token: {e}") from e
    if header.get("alg") not in {"RS256", "RS384", "RS512"}:
        raise ClerkAuthError(f"disallowed alg: {header.get('alg')}")
    kid = header.get("kid")
    if not kid:
        raise ClerkAuthError("missing kid")
    keys = _get_jwks_keys()
    pub = keys.get(kid)
    if pub is None:
        raise ClerkAuthError("unknown kid")
    # Issuer is enforced only when configured (back-compat: blank = skip).
    decode_kwargs: dict[str, Any] = {
        "algorithms": ["RS256", "RS384", "RS512"],
        "options": {"require": ["exp", "sub"]},
    }
    if settings.CLERK_ISSUER:
        decode_kwargs["issuer"] = settings.CLERK_ISSUER
        decode_kwargs["options"]["require"].append("iss")
    try:
        payload = pyjwt.decode(token, pub, **decode_kwargs)
    except pyjwt.ExpiredSignatureError as e:
        raise ClerkAuthError("token expired") from e
    except pyjwt.InvalidTokenError as e:
        raise ClerkAuthError(f"invalid token: {e}") from e
    # Authorized-party (azp) allowlist — blocks tokens minted for a different
    # origin on the same Clerk instance. Enforced only when configured.
    allowed_azp = settings.clerk_authorized_parties
    if allowed_azp and payload.get("azp") not in allowed_azp:
        raise ClerkAuthError("untrusted azp")
    return ClerkClaims(
        sub=payload["sub"],
        iss=payload.get("iss"),
        azp=payload.get("azp"),
        exp=payload["exp"],
        iat=payload.get("iat", 0),
        raw=payload,
    )
