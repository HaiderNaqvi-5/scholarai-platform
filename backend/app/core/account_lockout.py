"""Account-lockout (S8) — Redis sliding window per email.

After ``AUTH_LOCKOUT_MAX_FAILURES`` failed logins inside
``AUTH_LOCKOUT_WINDOW_SECONDS``, the account is locked for
``AUTH_LOCKOUT_DURATION_SECONDS``. The lock survives across the
``AUTH_RATE_LIMIT_LOGIN_REQUESTS`` per-IP rate limiter because attackers
with rotating IPs would otherwise sidestep the IP throttle entirely.

Failures and lock state are keyed off the lowercased email so case
variation can't bypass. Redis errors fail-open (logged, no block) so an
infra outage doesn't lock everyone out.
"""

import logging
from typing import Final

import redis.asyncio as redis

from app.core.config import settings


logger = logging.getLogger(__name__)

_FAIL_KEY: Final = "auth_lockout:fail:{email}"
_LOCK_KEY: Final = "auth_lockout:lock:{email}"

_redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def _normalize(email: str) -> str:
    return (email or "").strip().lower()


async def is_locked(email: str) -> bool:
    """Return True if the email is currently under lockout."""
    key = _LOCK_KEY.format(email=_normalize(email))
    try:
        return (await _redis_client.get(key)) is not None
    except redis.RedisError as exc:
        logger.warning("Account-lockout check failed for %s: %s", email, exc)
        return False


async def register_failure(email: str) -> bool:
    """Increment failure counter; lock account on threshold breach.

    Returns True when the call tripped the lock (so caller can craft a
    distinct error message if desired).
    """
    norm = _normalize(email)
    fail_key = _FAIL_KEY.format(email=norm)
    lock_key = _LOCK_KEY.format(email=norm)
    try:
        async with _redis_client.pipeline(transaction=True) as pipe:
            await pipe.incr(fail_key)
            await pipe.expire(fail_key, settings.AUTH_LOCKOUT_WINDOW_SECONDS)
            result = await pipe.execute()
        current = int(result[0]) if result and result[0] is not None else 0
        if current >= settings.AUTH_LOCKOUT_MAX_FAILURES:
            await _redis_client.set(
                lock_key, "1", ex=settings.AUTH_LOCKOUT_DURATION_SECONDS
            )
            await _redis_client.delete(fail_key)
            return True
    except redis.RedisError as exc:
        logger.warning("Account-lockout increment failed for %s: %s", email, exc)
    return False


async def clear(email: str) -> None:
    """Wipe failure counter + lock on successful login."""
    norm = _normalize(email)
    try:
        await _redis_client.delete(
            _FAIL_KEY.format(email=norm),
            _LOCK_KEY.format(email=norm),
        )
    except redis.RedisError as exc:
        logger.warning("Account-lockout clear failed for %s: %s", email, exc)
