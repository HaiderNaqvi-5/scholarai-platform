"""Firecrawl Cloud capture path. Replaces Playwright in ``_capture_source_once``.

The retry classification at ``service.py:_classify_capture_error`` already
distinguishes server / rate-limited / client / transient errors via
``httpx.HTTPStatusError`` and ``httpx`` transport exceptions. To stay inside
that contract, the Firecrawl client raises ``httpx.HTTPStatusError`` on any
non-2xx Firecrawl response — including a synthesized 502 when Firecrawl
returns ``{"success": false}`` in a 200 body.
"""
from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest

from app.services.ingestion.firecrawl_capture import (
    FirecrawlNotConfiguredError,
    firecrawl_capture,
)
from app.utils.url_safety import UnsafeURLError


class _AsyncClientStub:
    """Records the POST sent to Firecrawl and returns a scripted response."""

    instances: list["_AsyncClientStub"] = []

    def __init__(
        self,
        *,
        status_code: int = 200,
        body: dict | None = None,
        raise_exc: Exception | None = None,
    ):
        self.status_code = status_code
        self.body = body or {}
        self.raise_exc = raise_exc
        self.posted: list[tuple[str, dict, dict]] = []
        type(self).instances.append(self)

    def factory(self, *args, **kwargs):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def post(self, url, *, headers=None, json=None):  # noqa: A002 - mirrors httpx kw
        if self.raise_exc is not None:
            raise self.raise_exc
        self.posted.append((url, headers or {}, json or {}))
        request = httpx.Request("POST", url, json=json)
        return httpx.Response(
            self.status_code,
            content=_dumps(self.body),
            request=request,
        )


def _dumps(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _settings(api_key: str = "fc-test-key", url: str = "https://api.firecrawl.dev"):
    """Patch ``firecrawl_capture.settings`` for a single test."""
    from app.services.ingestion import firecrawl_capture as mod

    settings = mod.settings
    return patch.multiple(
        settings,
        FIRECRAWL_API_KEY=api_key,
        FIRECRAWL_API_URL=url,
        FIRECRAWL_TIMEOUT_SECONDS=60.0,
    )


def _public_dns():
    return patch(
        "app.utils.url_safety.socket.getaddrinfo",
        return_value=[(2, 1, 0, "", ("93.184.216.34", 0))],
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_capture_result_on_success() -> None:
    stub = _AsyncClientStub(
        status_code=200,
        body={
            "success": True,
            "data": {
                "markdown": "# Chevening Scholarships",
                "html": "<html><body>x</body></html>",
                "metadata": {
                    "sourceURL": "https://www.chevening.org/scholarships/",
                    "title": "Chevening Scholarships",
                    "statusCode": 200,
                },
            },
        },
    )
    _AsyncClientStub.instances = []
    with (
        _settings(),
        _public_dns(),
        patch(
            "app.services.ingestion.firecrawl_capture.httpx.AsyncClient",
            side_effect=stub.factory,
        ),
    ):
        result = await firecrawl_capture(
            "https://www.chevening.org/scholarships/", attempt=1
        )

    assert result.capture_mode == "firecrawl"
    assert result.html == "<html><body>x</body></html>"
    assert result.final_url == "https://www.chevening.org/scholarships/"
    assert result.title == "Chevening Scholarships"
    assert result.metadata["status_code"] == 200
    assert result.metadata["attempt"] == 1
    # The POST must carry the API key as a bearer token.
    sent_url, sent_headers, sent_body = stub.posted[0]
    assert sent_url.endswith("/v1/scrape")
    assert sent_headers["Authorization"] == "Bearer fc-test-key"
    assert sent_body["url"] == "https://www.chevening.org/scholarships/"
    assert "markdown" in sent_body["formats"]


# ---------------------------------------------------------------------------
# SSRF rejection: validator runs BEFORE the vendor call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ssrf_url_rejected_before_vendor_call() -> None:
    stub = _AsyncClientStub(status_code=200, body={"success": True, "data": {}})
    _AsyncClientStub.instances = []
    with (
        _settings(),
        patch(
            "app.utils.url_safety.socket.getaddrinfo",
            return_value=[(2, 1, 0, "", ("169.254.169.254", 0))],
        ),
        patch(
            "app.services.ingestion.firecrawl_capture.httpx.AsyncClient",
            side_effect=stub.factory,
        ),
    ):
        with pytest.raises(UnsafeURLError):
            await firecrawl_capture("http://attacker.example/", attempt=1)
    # Vendor was never contacted — no metadata leakage to Firecrawl logs.
    assert stub.posted == []


# ---------------------------------------------------------------------------
# Error mapping — feeds the existing _classify_capture_error / retry wrapper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_429_raises_http_status_error() -> None:
    stub = _AsyncClientStub(status_code=429, body={"success": False, "error": "rate"})
    _AsyncClientStub.instances = []
    with (
        _settings(),
        _public_dns(),
        patch(
            "app.services.ingestion.firecrawl_capture.httpx.AsyncClient",
            side_effect=stub.factory,
        ),
    ):
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await firecrawl_capture("https://public.example/", attempt=1)
    assert exc_info.value.response.status_code == 429


@pytest.mark.asyncio
async def test_5xx_raises_http_status_error() -> None:
    stub = _AsyncClientStub(status_code=503, body={"success": False, "error": "down"})
    _AsyncClientStub.instances = []
    with (
        _settings(),
        _public_dns(),
        patch(
            "app.services.ingestion.firecrawl_capture.httpx.AsyncClient",
            side_effect=stub.factory,
        ),
    ):
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await firecrawl_capture("https://public.example/", attempt=1)
    assert exc_info.value.response.status_code == 503


@pytest.mark.asyncio
async def test_4xx_raises_http_status_error() -> None:
    stub = _AsyncClientStub(status_code=403, body={"success": False, "error": "forbidden"})
    _AsyncClientStub.instances = []
    with (
        _settings(),
        _public_dns(),
        patch(
            "app.services.ingestion.firecrawl_capture.httpx.AsyncClient",
            side_effect=stub.factory,
        ),
    ):
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await firecrawl_capture("https://public.example/", attempt=1)
    assert exc_info.value.response.status_code == 403


@pytest.mark.asyncio
async def test_success_false_in_200_body_raises() -> None:
    # Firecrawl occasionally returns HTTP 200 with success=false — treat as
    # bad-gateway equivalent so the capture retry wrapper still sees a
    # classifiable error rather than silently returning an empty CaptureResult.
    stub = _AsyncClientStub(
        status_code=200,
        body={"success": False, "error": "browser timeout"},
    )
    _AsyncClientStub.instances = []
    with (
        _settings(),
        _public_dns(),
        patch(
            "app.services.ingestion.firecrawl_capture.httpx.AsyncClient",
            side_effect=stub.factory,
        ),
    ):
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await firecrawl_capture("https://public.example/", attempt=1)
    assert exc_info.value.response.status_code == 502


# ---------------------------------------------------------------------------
# Missing API key — no silent log-only fallback for the scraper path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_raises_when_api_key_missing() -> None:
    with _settings(api_key=""):
        with pytest.raises(FirecrawlNotConfiguredError):
            await firecrawl_capture("https://public.example/", attempt=1)
