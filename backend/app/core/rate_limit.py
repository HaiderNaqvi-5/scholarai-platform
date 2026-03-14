from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

DEFAULT_RATE_LIMIT = f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
AUTH_RATE_LIMIT = f"{settings.RATE_LIMIT_AUTH_PER_MINUTE}/minute"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_RATE_LIMIT],
)
