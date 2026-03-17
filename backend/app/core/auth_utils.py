import time
from app.core.rate_limit import redis_client
from app.core.config import settings

BLACKLIST_NAMESPACE = "token_blacklist"

async def blacklist_token(jti: str, expires_at: int) -> None:
    """
    Blacklist a token ID until its expiration.
    
    :param jti: The unique JWT ID
    :param expires_at: Unix timestamp of token expiration
    """
    now = int(time.time())
    ttl = expires_at - now
    if ttl > 0:
        await redis_client.setex(f"{BLACKLIST_NAMESPACE}:{jti}", ttl, "true")

async def is_token_blacklisted(jti: str) -> bool:
    """Check if a token ID is in the blacklist."""
    if not jti:
        return False
    return await redis_client.exists(f"{BLACKLIST_NAMESPACE}:{jti}") > 0
