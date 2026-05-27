"""SSRF guard for outbound fetches in the ingestion path.

Closes C1 (and H8) in ``security-audit.md``. Every URL the scraper or
discovery helper is about to hit must pass :func:`assert_public_url` so an
admin cannot register ``http://169.254.169.254/`` or ``http://127.0.0.1/``
and have the response body echoed back through the curator UI.

Use :func:`safe_get` instead of a raw ``httpx.AsyncClient(follow_redirects=True)``
when fetching robots.txt, sitemaps, RSS feeds, or any other in-process HTTP
resource — it walks the redirect chain manually and re-validates every hop
(defeats DNS rebind via redirect).
"""
from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_DEFAULT_MAX_REDIRECTS = 5
_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_USER_AGENT = "ScholarAI-Internal-Ingestion/0.1"

# Ranges that ``ipaddress`` does not flag via the ``is_*`` properties in every
# stdlib version we ship against, but that we still must reject. CGNAT
# (RFC 6598) is the notable example — not in ``is_private`` for Python ≤ 3.13.
_EXTRA_BLOCKED_NETWORKS = (
    ipaddress.ip_network("100.64.0.0/10"),     # RFC 6598 shared CGNAT
    ipaddress.ip_network("198.18.0.0/15"),     # RFC 2544 benchmarking
)


class UnsafeURLError(ValueError):
    """Raised when a URL targets a private/loopback/reserved address."""


def assert_public_url(url: str) -> str:
    """Return the canonical URL if it is safe to fetch from the API process.

    Rejects non-http(s) schemes, missing hosts, embedded userinfo, and any
    hostname whose DNS resolution includes a private, loopback, link-local,
    multicast, or otherwise reserved address — for either IPv4 or IPv6.

    Raises :class:`UnsafeURLError` with a short message suitable for logging
    (does not leak the resolved IP back to the request payload).
    """
    if not isinstance(url, str) or not url.strip():
        raise UnsafeURLError("url is empty")

    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise UnsafeURLError(f"scheme {scheme!r} not allowed")
    if parsed.username or parsed.password:
        raise UnsafeURLError("url must not embed userinfo")
    host = (parsed.hostname or "").strip()
    if not host:
        raise UnsafeURLError("url is missing host")

    for ip in _resolve_all(host):
        if _is_private_address(ip):
            raise UnsafeURLError("url resolves to a non-public address")

    return urlunparse(
        (
            scheme,
            parsed.netloc,
            parsed.path or "/",
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


async def safe_get(
    url: str,
    *,
    max_redirects: int = _DEFAULT_MAX_REDIRECTS,
    timeout: float = _DEFAULT_TIMEOUT_SECONDS,
    headers: dict[str, str] | None = None,
    user_agent: str = _DEFAULT_USER_AGENT,
) -> httpx.Response:
    """GET ``url`` with manual redirect handling and SSRF re-validation per hop.

    Differs from ``httpx.AsyncClient(follow_redirects=True)`` in three ways
    that matter for the SSRF threat model:

    1. Every hop's URL is passed through :func:`assert_public_url` before the
       HTTP request is issued. A 302 from a public host to ``127.0.0.1`` is
       rejected on the *next* iteration, not after the inner socket is opened.
    2. The redirect chain is capped at ``max_redirects`` (default 5) regardless
       of httpx's own defaults.
    3. ``verify=False`` is *never* used. The old silent TLS-bypass retry
       (audit H8) is gone — a TLS failure surfaces as ``httpx.HTTPError``.
    """
    current_url = assert_public_url(url)
    merged_headers = {"User-Agent": user_agent}
    if headers:
        merged_headers.update(headers)

    last_response: httpx.Response | None = None
    for hop in range(max_redirects + 1):
        async with httpx.AsyncClient(follow_redirects=False, timeout=timeout) as client:
            response = await client.get(current_url, headers=merged_headers)
        last_response = response
        if response.status_code not in (301, 302, 303, 307, 308):
            return response
        location = response.headers.get("location")
        if not location:
            return response
        next_url = str(httpx.URL(current_url).join(location))
        current_url = assert_public_url(next_url)

    raise UnsafeURLError(
        f"redirect chain exceeded {max_redirects} hops"
        + (f" (last status {last_response.status_code})" if last_response else "")
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_all(host: str) -> list[str]:
    """Return every IP ``getaddrinfo`` knows for ``host`` (IPv4 + IPv6).

    Literal IPs short-circuit DNS so a malicious ``http://127.0.0.1/`` URL
    still gets rejected even when DNS is unavailable.
    """
    try:
        ipaddress.ip_address(host)
        return [host]
    except ValueError:
        pass

    try:
        infos: list[Any] = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"host {host!r} did not resolve") from exc

    ips: list[str] = []
    for entry in infos:
        sockaddr = entry[4]
        if sockaddr and isinstance(sockaddr, tuple):
            ips.append(sockaddr[0])
    if not ips:
        raise UnsafeURLError(f"host {host!r} did not resolve")
    return ips


def _is_private_address(raw: str) -> bool:
    try:
        ip = ipaddress.ip_address(raw)
    except ValueError:
        # Anything we cannot parse as an IP is treated as unsafe — better to
        # over-reject than allow a string that bypassed our DNS check.
        return True
    # IPv4-mapped IPv6 (``::ffff:127.0.0.1``) — re-check the embedded IPv4
    # because ``is_loopback`` on the mapped form is True but ``is_private``
    # only inspects the IPv6 view.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True
    return any(ip in network for network in _EXTRA_BLOCKED_NETWORKS)
