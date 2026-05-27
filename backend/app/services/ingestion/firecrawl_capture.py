"""Firecrawl Cloud capture path for the ingestion scraper.

Replaces the Playwright + Chromium launcher that used to live inside
``_capture_source_once``. Behavioural contract:

* The URL is run through :func:`assert_public_url` *before* the vendor call so
  ``127.0.0.1`` / ``169.254.169.254`` never leak into Firecrawl's logs.
* Any non-2xx HTTP status — and any ``{"success": false}`` body — surfaces as
  ``httpx.HTTPStatusError`` so the existing
  ``IngestionService._classify_capture_error`` / retry wrapper can decide
  whether to retry without learning about Firecrawl as a concept.
* Missing ``FIRECRAWL_API_KEY`` is a hard error; the scraper has no other
  capture path after the Playwright removal.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.services.ingestion.types import CaptureResult
from app.utils.url_safety import assert_public_url

_SCRAPE_PATH = "/v1/scrape"
_DEFAULT_FORMATS = ("markdown", "html")


class FirecrawlNotConfiguredError(RuntimeError):
    """Raised when no FIRECRAWL_API_KEY is configured for the current env."""


async def firecrawl_capture(url: str, *, attempt: int = 1) -> CaptureResult:
    """Fetch ``url`` via Firecrawl Cloud and return a :class:`CaptureResult`.

    See module docstring for the error contract.
    """
    api_key = (settings.FIRECRAWL_API_KEY or "").strip()
    if not api_key:
        raise FirecrawlNotConfiguredError(
            "FIRECRAWL_API_KEY is not set — scraper capture path disabled"
        )

    safe_url = assert_public_url(url)

    endpoint = settings.FIRECRAWL_API_URL.rstrip("/") + _SCRAPE_PATH
    timeout_seconds = float(settings.FIRECRAWL_TIMEOUT_SECONDS)
    payload = {
        "url": safe_url,
        "formats": list(_DEFAULT_FORMATS),
        "onlyMainContent": False,
        "timeout": int(timeout_seconds * 1000),
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=timeout_seconds + 5.0) as client:
        response = await client.post(endpoint, headers=headers, json=payload)

    body = _safe_json(response)
    if not response.is_success:
        raise httpx.HTTPStatusError(
            f"Firecrawl returned HTTP {response.status_code}",
            request=response.request,
            response=response,
        )
    if not body.get("success", False):
        raise httpx.HTTPStatusError(
            f"Firecrawl call failed: {body.get('error') or 'unknown error'}",
            request=response.request,
            response=httpx.Response(502, request=response.request),
        )

    data = body.get("data") or {}
    metadata = data.get("metadata") or {}
    html = data.get("html") or ""
    final_url = (
        metadata.get("sourceURL")
        or metadata.get("url")
        or safe_url
    )
    title = metadata.get("title") or metadata.get("ogTitle")
    upstream_status = metadata.get("statusCode")

    return CaptureResult(
        html=html,
        final_url=final_url,
        title=title,
        capture_mode="firecrawl",
        metadata={
            "requested_url": safe_url,
            "final_url": final_url,
            "page_title": title,
            "status_code": upstream_status if isinstance(upstream_status, int) else response.status_code,
            "attempt": attempt,
            "transport_errors": [],
            "firecrawl": {
                "endpoint": endpoint,
                "credits": body.get("creditsUsed"),
                "markdown_length": len(data.get("markdown") or ""),
            },
        },
    )


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        parsed = response.json()
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
