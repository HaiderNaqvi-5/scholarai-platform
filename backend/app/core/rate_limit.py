import logging

from fastapi import Request, status
import redis.asyncio as redis
from app.core.config import settings
from scholarai_common.errors import ScholarAIException, ErrorCode

# Initialize redis connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int, *, fail_open: bool = True):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.fail_open = fail_open

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{request.url.path}:{client_ip}"
        
        try:
            current = await redis_client.get(key)
            if current and int(current) >= self.requests_limit:
                raise ScholarAIException(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Too many requests. Please try again later.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            
            async with redis_client.pipeline(transaction=True) as pipe:
                await pipe.incr(key)
                if not current:
                    await pipe.expire(key, self.window_seconds)
                await pipe.execute()
        except redis.RedisError as exc:
            logger.warning("Rate limiter unavailable for %s: %s", request.url.path, exc)
            if self.fail_open:
                return
            raise ScholarAIException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Rate limiter is temporarily unavailable. Please retry shortly.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
