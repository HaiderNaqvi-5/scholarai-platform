import hashlib
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)
_HIBP_URL = "https://api.pwnedpasswords.com/range/{prefix}"


async def _fetch_range(prefix: str, timeout: float) -> bytes:
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.get(_HIBP_URL.format(prefix=prefix), headers={"Add-Padding": "true"})
        r.raise_for_status()
        return r.content


async def is_pwned(password: str, *, timeout: float | None = None) -> bool:
    """Return True if password appears in HIBP. Fail-open on network error."""
    digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = digest[:5], digest[5:]
    try:
        body = await _fetch_range(prefix, timeout or settings.HIBP_TIMEOUT_SECONDS)
    except Exception as exc:  # noqa: BLE001
        logger.warning("hibp.fail_open", extra={"err": str(exc)})
        return False
    for line in body.splitlines():
        line_s = line.decode("ascii", errors="ignore")
        cand = line_s.split(":", 1)[0].strip()
        if cand == suffix:
            return True
    return False
