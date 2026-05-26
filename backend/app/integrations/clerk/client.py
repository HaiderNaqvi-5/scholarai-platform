from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:
    from clerk_backend_api import Clerk


@lru_cache(maxsize=1)
def clerk_client() -> "Clerk":
    """Return a cached Clerk SDK client.

    The import is deferred so the module is importable even when the
    clerk-backend-api package is not installed (e.g. unit-test environments
    that mock the clerk_api parameter directly).
    """
    try:
        from clerk_backend_api import Clerk  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "clerk-backend-api is not installed. "
            "Run: pip install clerk-backend-api==1.6.0"
        ) from exc
    if not settings.CLERK_SECRET_KEY:
        raise RuntimeError("CLERK_SECRET_KEY not configured")
    return Clerk(bearer_auth=settings.CLERK_SECRET_KEY)
