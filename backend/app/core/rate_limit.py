import logging

from fastapi import Request, status
import redis.asyncio as redis
from app.core.config import settings
from scholarai_common.errors import ScholarAIException, ErrorCode

# Initialize redis connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
logger = logging.getLogger(__name__)

# Atomic fixed-window counter: INCR the key, and on the first hit (count == 1)
# set the window TTL. Returns the post-increment count. Single round trip ->
# no GET-then-INCR TOCTOU; concurrent callers cannot exceed the limit because
# the authoritative counter is returned before the request is allowed to proceed.
_INCR_WITH_EXPIRE_LUA = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


def _client_ip(request: Request) -> str:
    """Real client IP. Trust the left-most X-Forwarded-For entry only when
    TRUSTED_PROXY_HOPS > 0 (mirrors api/v1/routes/geo.py:_client_ip and the
    S20 ProxyHeadersMiddleware gate in main.py). Otherwise use the socket peer,
    so a spoofed XFF header cannot share or evade another client's bucket."""
    if settings.TRUSTED_PROXY_HOPS > 0:
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            first = fwd.split(",")[0].strip()
            if first:
                return first
    if request.client:
        return request.client.host
    return "unknown"


def _subject(request: Request) -> str:
    """Bucket identity. Prefer the authenticated user (request.state.current_user
    set by the route) so per-user limits survive IP changes / shared NAT;
    fall back to the trusted client IP for unauthenticated routes (auth.py)."""
    user = getattr(request.state, "current_user", None)
    user_id = getattr(user, "id", None)
    if user_id is not None:
        return f"user:{user_id}"
    return f"ip:{_client_ip(request)}"


class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int, *, fail_open: bool = True):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.fail_open = fail_open

    async def __call__(self, request: Request):
        key = f"rate_limit:{request.url.path}:{_subject(request)}"

        try:
            count = await redis_client.eval(
                _INCR_WITH_EXPIRE_LUA, 1, key, self.window_seconds
            )
        except redis.RedisError as exc:
            if self.fail_open:
                logger.warning("rate_limit.redis_unavailable_fail_open path=%s: %s", request.url.path, exc)
                return
            logger.warning(
                "rate_limit.redis_unavailable_fail_closed path=%s — denying request (degraded mode): %s",
                request.url.path,
                exc,
            )
            raise ScholarAIException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Rate limiter is temporarily unavailable. Please retry shortly.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc

        if int(count) > self.requests_limit:
            raise ScholarAIException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Too many requests. Please try again later.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
