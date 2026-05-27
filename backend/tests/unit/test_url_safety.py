"""SSRF guard for the ingestion scraper. Covers C1 in security-audit.md.

The validator must reject any URL whose hostname resolves to a private,
loopback, link-local, or otherwise reserved address space — and must
re-validate every redirect hop in ``safe_get`` so an attacker cannot chain a
public host that 302s to ``169.254.169.254`` (cloud metadata) or
``127.0.0.1``.

These tests mock ``socket.getaddrinfo`` so they are deterministic and never
touch the network.
"""
from __future__ import annotations

import socket
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.utils.url_safety import (
    UnsafeURLError,
    assert_public_url,
    safe_get,
)


def _addrinfo(*ips: str) -> list:
    """Build a getaddrinfo-style return list from raw IP strings.

    Real ``socket.getaddrinfo`` returns 5-tuples; we mimic the shape
    ``(family, type, proto, canonname, sockaddr)`` so the validator can
    iterate without special-casing.
    """
    out = []
    for ip in ips:
        family = socket.AF_INET6 if ":" in ip else socket.AF_INET
        sockaddr = (ip, 0, 0, 0) if family == socket.AF_INET6 else (ip, 0)
        out.append((family, socket.SOCK_STREAM, 0, "", sockaddr))
    return out


# ---------------------------------------------------------------------------
# assert_public_url — scheme / shape checks (no DNS needed)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/",
        "file:///etc/passwd",
        "gopher://example.com/",
        "javascript:alert(1)",
        "data:text/plain,hi",
        "://no-scheme",
        "",
        "   ",
    ],
)
def test_rejects_non_http_schemes(url: str) -> None:
    with pytest.raises(UnsafeURLError):
        assert_public_url(url)


def test_rejects_userinfo_in_url() -> None:
    # ``http://attacker.com@127.0.0.1/`` parses with attacker.com as userinfo
    # and 127.0.0.1 as host — DNS check alone would miss this on some libs.
    with pytest.raises(UnsafeURLError):
        assert_public_url("http://attacker.com@127.0.0.1/admin")


def test_rejects_missing_host() -> None:
    with pytest.raises(UnsafeURLError):
        assert_public_url("http:///path")


# ---------------------------------------------------------------------------
# assert_public_url — DNS-resolved IP rejection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",        # loopback
        "127.0.0.5",        # loopback /8
        "10.0.0.1",         # RFC1918
        "10.255.255.255",
        "172.16.0.1",       # RFC1918
        "172.31.255.254",
        "192.168.1.1",      # RFC1918
        "169.254.169.254",  # AWS / GCP / Azure metadata
        "169.254.0.5",      # link-local
        "0.0.0.0",          # "this network"
        "100.64.0.1",       # CGNAT
        "224.0.0.1",        # multicast
        "240.0.0.1",        # reserved
        "255.255.255.255",  # broadcast
    ],
)
def test_rejects_private_ipv4(ip: str) -> None:
    with patch("app.utils.url_safety.socket.getaddrinfo", return_value=_addrinfo(ip)):
        with pytest.raises(UnsafeURLError):
            assert_public_url(f"http://attacker.example/{ip}")


@pytest.mark.parametrize(
    "ip",
    [
        "::1",                  # loopback
        "fc00::1",              # unique local /7
        "fd12:3456::1",         # unique local
        "fe80::1",              # link-local /10
        "::ffff:127.0.0.1",     # IPv4-mapped loopback
        "::ffff:169.254.169.254",
        "ff00::1",              # multicast
    ],
)
def test_rejects_private_ipv6(ip: str) -> None:
    with patch("app.utils.url_safety.socket.getaddrinfo", return_value=_addrinfo(ip)):
        with pytest.raises(UnsafeURLError):
            assert_public_url("http://attacker.example/")


def test_rejects_when_any_resolved_ip_is_private() -> None:
    # DNS rebind defense: even if one A-record is public, a single private
    # answer is enough to block — the client cannot choose which address it
    # connects to on retry.
    with patch(
        "app.utils.url_safety.socket.getaddrinfo",
        return_value=_addrinfo("8.8.8.8", "127.0.0.1"),
    ):
        with pytest.raises(UnsafeURLError):
            assert_public_url("http://mixed.example/")


def test_rejects_unresolvable_host() -> None:
    with patch(
        "app.utils.url_safety.socket.getaddrinfo",
        side_effect=socket.gaierror("nodename nor servname provided"),
    ):
        with pytest.raises(UnsafeURLError):
            assert_public_url("http://nx.example.invalid/")


def test_accepts_public_host() -> None:
    with patch(
        "app.utils.url_safety.socket.getaddrinfo",
        return_value=_addrinfo("104.18.0.10"),
    ):
        canonical = assert_public_url("https://www.chevening.org/scholarships/")
    assert canonical.startswith("https://www.chevening.org/")


def test_accepts_public_ipv6() -> None:
    with patch(
        "app.utils.url_safety.socket.getaddrinfo",
        return_value=_addrinfo("2606:4700::1111"),
    ):
        canonical = assert_public_url("https://example.org/page")
    assert canonical == "https://example.org/page"


# ---------------------------------------------------------------------------
# safe_get — redirect chain validation
# ---------------------------------------------------------------------------


class _StubResponse:
    """Minimal stand-in for httpx.Response covering what safe_get reads."""

    def __init__(
        self,
        *,
        status_code: int,
        text: str = "",
        url: str = "https://example.org/",
        headers: dict | None = None,
    ):
        self.status_code = status_code
        self.text = text
        self.url = httpx.URL(url)
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if 400 <= self.status_code < 600:
            raise httpx.HTTPStatusError(
                f"{self.status_code}",
                request=httpx.Request("GET", str(self.url)),
                response=httpx.Response(self.status_code, request=httpx.Request("GET", str(self.url))),
            )


class _FakeClient:
    """Async-context client that returns a scripted sequence of responses.

    Records all constructor invocations across re-instantiation so tests can
    assert on ``follow_redirects`` / ``verify`` kwargs even when ``safe_get``
    opens a fresh client per redirect hop.
    """

    constructor_kwargs: list[dict] = []
    requested_urls: list[str] = []

    def __init__(self, responses: list[_StubResponse]):
        self._responses = list(responses)
        type(self).constructor_kwargs = []
        type(self).requested_urls = []

    def factory(self, *args, **kwargs):
        type(self).constructor_kwargs.append(kwargs)
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def get(self, url, headers=None):
        type(self).requested_urls.append(str(url))
        if not self._responses:
            raise AssertionError(f"unexpected extra GET to {url}")
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_safe_get_follows_safe_redirect() -> None:
    responses = [
        _StubResponse(
            status_code=302,
            url="https://public.example/",
            headers={"location": "https://public.example/final"},
        ),
        _StubResponse(status_code=200, text="ok", url="https://public.example/final"),
    ]
    fake = _FakeClient(responses)
    with (
        patch(
            "app.utils.url_safety.socket.getaddrinfo",
            return_value=_addrinfo("93.184.216.34"),
        ),
        patch("app.utils.url_safety.httpx.AsyncClient", side_effect=fake.factory),
    ):
        response = await safe_get("https://public.example/")
    assert response.status_code == 200
    assert response.text == "ok"
    # Manual redirect loop must disable httpx's own redirect handling.
    for kwargs in _FakeClient.constructor_kwargs:
        assert kwargs.get("follow_redirects") is False
    # One client per hop: initial + 1 redirect follow = 2 instantiations.
    assert len(_FakeClient.constructor_kwargs) == 2


@pytest.mark.asyncio
async def test_safe_get_rejects_redirect_to_private_host() -> None:
    # Hop 1: public host returns 302 to metadata IP.
    redirect = _StubResponse(
        status_code=302,
        url="https://public.example/",
        headers={"location": "http://169.254.169.254/latest/meta-data/"},
    )
    fake = _FakeClient([redirect])

    def addrinfo(host, *_a, **_kw):
        return _addrinfo("93.184.216.34" if "public" in host else "169.254.169.254")

    with (
        patch("app.utils.url_safety.socket.getaddrinfo", side_effect=addrinfo),
        patch("app.utils.url_safety.httpx.AsyncClient", side_effect=fake.factory),
    ):
        with pytest.raises(UnsafeURLError):
            await safe_get("https://public.example/")
    # Exactly one GET issued — the redirect target was rejected before fetch.
    assert len(_FakeClient.requested_urls) == 1


@pytest.mark.asyncio
async def test_safe_get_caps_redirect_chain() -> None:
    # 10-hop chain; cap is 5 so loop must abort.
    responses = [
        _StubResponse(
            status_code=302,
            url=f"https://public.example/{i}",
            headers={"location": f"https://public.example/{i + 1}"},
        )
        for i in range(10)
    ]
    fake = _FakeClient(responses)
    with (
        patch(
            "app.utils.url_safety.socket.getaddrinfo",
            return_value=_addrinfo("93.184.216.34"),
        ),
        patch("app.utils.url_safety.httpx.AsyncClient", side_effect=fake.factory),
    ):
        with pytest.raises(UnsafeURLError):
            await safe_get("https://public.example/0", max_redirects=5)
    # Hops: initial + 5 redirect follows = 6 GETs before abort.
    assert len(_FakeClient.requested_urls) == 6


@pytest.mark.asyncio
async def test_safe_get_never_disables_tls_verify() -> None:
    fake = _FakeClient([_StubResponse(status_code=200, url="https://public.example/")])
    with (
        patch(
            "app.utils.url_safety.socket.getaddrinfo",
            return_value=_addrinfo("93.184.216.34"),
        ),
        patch("app.utils.url_safety.httpx.AsyncClient", side_effect=fake.factory),
    ):
        await safe_get("https://public.example/")
    # Confirm we never instantiate with verify=False (closes audit H8).
    for kwargs in _FakeClient.constructor_kwargs:
        assert kwargs.get("verify", True) is not False
