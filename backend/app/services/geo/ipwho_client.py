"""ipwho.is async client with Redis cache + safe fallback.

Resolves an IPv4/IPv6 address to (currency_code, country_code). Returns
(None, None) on lookup failure; the route layer applies the PKR fallback.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional, Tuple

import httpx
import redis.asyncio as redis

from app.core.config import settings

log = logging.getLogger(__name__)

IPWHO_URL = "https://ipwho.is/{ip}?fields=success,country_code,currency"
CACHE_KEY_PREFIX = "geo:currency:"
CACHE_TTL_SECONDS = 3600  # 1h

# Single shared client. decode_responses=True so cache values are str.
_redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def _redact_ip(ip: str) -> str:
    """Stable, non-reversible token for an IP (GEO-IP-LEAK).

    Used for the cache key and log lines so the raw IP of an unauthenticated,
    pre-consent visitor is never persisted in Redis or written to logs. Stable
    per IP so the 1h cache still hits.
    """
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


def _cache_key(ip: str) -> str:
    return f"{CACHE_KEY_PREFIX}{_redact_ip(ip)}"


async def _read_cache(ip: str) -> Optional[Tuple[Optional[str], Optional[str]]]:
    try:
        cached = await _redis_client.get(_cache_key(ip))
    except redis.RedisError as exc:
        log.warning("geo cache read failed for ip=%s: %s", _redact_ip(ip), exc)
        return None
    if not cached:
        return None
    parts = cached.split("|", 1)
    if len(parts) != 2:
        return None
    currency = parts[0] or None
    country = parts[1] or None
    return currency, country


async def _write_cache(ip: str, currency: Optional[str], country: Optional[str]) -> None:
    try:
        await _redis_client.set(
            _cache_key(ip),
            f"{currency or ''}|{country or ''}",
            ex=CACHE_TTL_SECONDS,
        )
    except redis.RedisError as exc:
        log.warning("geo cache write failed for ip=%s: %s", _redact_ip(ip), exc)


async def resolve_currency(
    ip: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """Return (currency_code, country_code) for the given IP.

    1h Redis cache per IP. Returns (None, None) on lookup failure so the
    caller can apply a default. Never raises — fail-soft for UX.
    """
    if not ip:
        return None, None

    cached = await _read_cache(ip)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(IPWHO_URL.format(ip=ip))
            data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("geo lookup failed for ip=%s: %s", _redact_ip(ip), exc)
        return None, None

    if not isinstance(data, dict) or not data.get("success"):
        return None, None

    currency_field = data.get("currency") or {}
    currency = currency_field.get("code") if isinstance(currency_field, dict) else None
    country = data.get("country_code")

    await _write_cache(ip, currency, country)
    return currency, country
