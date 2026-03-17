import time
from fastapi import Request
import redis.asyncio as redis
from app.core.config import settings
from scholarai_common.errors import ScholarAIException, ErrorCode

# Initialize redis connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    async def __call__(self, request: Request):
        if settings.ENVIRONMENT == "development" and not settings.DEBUG:
            # Optionally skip in dev, but let's keep it for testing if needed
            pass
            
        client_ip = request.client.host
        key = f"rate_limit:{request.url.path}:{client_ip}"
        
        try:
            current = await redis_client.get(key)
            if current and int(current) >= self.requests_limit:
                raise ScholarAIException(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Too many requests. Please try again later.",
                    status_code=429
                )
            
            async with redis_client.pipeline(transaction=True) as pipe:
                await pipe.incr(key)
                if not current:
                    await pipe.expire(key, self.window_seconds)
                await pipe.execute()
        except redis.RedisError:
            # Fallback: if redis is down, we allow the request but log it
            # In a production system, you might want to switch to a tighter local cache
            pass
