"""GET /api/v1/geo/currency — IP -> currency proxy.

Backend resolves currency from the requester's IP (X-Forwarded-For when
behind a trusted proxy, otherwise request.client.host) via ipwho.is,
Redis-caches for 1h, falls back to PKR on lookup failure or unsupported
currency.

Eliminates the need for the frontend to call ipwho.is directly, which is
blocked by the S20 CSP `connect-src 'self' ${API_ORIGIN}` policy.
"""

from typing import Optional

from fastapi import APIRouter, Request

from app.services.geo import resolve_currency

router = APIRouter()

SUPPORTED = {"PKR", "GBP", "EUR", "AED", "USD"}


def _client_ip(request: Request) -> Optional[str]:
    """Pick the requester IP. Trusts X-Forwarded-For (left-most) when
    a TRUSTED_PROXY_HOPS > 0 setting was applied to ProxyHeadersMiddleware
    upstream (per S20). Otherwise uses the socket address.
    """
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        first = fwd.split(",")[0].strip()
        if first:
            return first
    if request.client:
        return request.client.host
    return None


@router.get("/currency")
async def get_currency(request: Request) -> dict[str, Optional[str]]:
    """Return ISO currency + country code for the requester's IP."""
    ip = _client_ip(request)
    currency, country = await resolve_currency(ip)
    return {
        "currency": currency if currency in SUPPORTED else "PKR",
        "country": country,
    }
