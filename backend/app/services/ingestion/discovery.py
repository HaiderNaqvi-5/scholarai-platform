"""DiscoveryService — surface candidate scholarship sources from a seed aggregator URL.

PR 3 of the scraper optimization pass. Given a seed URL (e.g. a government education portal
homepage or an aggregator like studyabroad.gov.pk), crawl one level deep, classify outbound
links by scholarship-likelihood, and return candidate ``SourceRegistry`` rows for human
review. No automatic registration — discovery surfaces, admins approve.

Classification path:
1. Extract outbound links (different host than seed) whose anchor text or URL contains a
   scope keyword (``scholarship``, ``award``, ``fellowship``, ``grant``, etc.).
2. If ``AnthropicClient.available`` → batch-classify via Haiku 4.5 with cache-controlled
   system prompt.
3. Otherwise → TLD + keyword heuristic (``.gov``, ``.edu``, ``.org`` get scored higher).

The service is read-only with respect to ``SourceRegistry`` — callers decide whether to
upsert. ``DiscoveryService.discover_new_sources`` returns a list of ``DiscoveredSource``
dataclasses ranked by confidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.anthropic_client import AnthropicClient


_SCOPE_KEYWORDS: tuple[str, ...] = (
    "scholarship",
    "award",
    "fellowship",
    "grant",
    "bursary",
    "stipend",
    "scheme",
)

_DISCOVERY_SYSTEM_PROMPT = (
    "You classify outbound links from a Pakistani scholarship-aggregator page.\n"
    "Goal: identify links that lead to ACTUAL scholarship-issuing organisations or "
    "scholarship listing pages — not blogs, news, contact pages, social media, or "
    "unrelated sites.\n\n"
    'Return strict JSON: {"candidates": [{"url", "name", "country_code", "confidence"}]}.\n'
    "- country_code: ISO-3166 alpha-2 of the host country (best guess; \"XX\" if unknown).\n"
    "- confidence: 0.0-1.0. Threshold below 0.5 should be dropped by the caller.\n"
    "- Skip blogs, news outlets, direct .pdf downloads, social media.\n"
    "- Prefer official .gov / .edu / .org domains.\n"
)


@dataclass
class DiscoveredSource:
    base_url: str
    display_name: str
    country_code: str
    confidence: float
    source_key_suggestion: str


class DiscoveryService:
    """Crawl a seed aggregator URL and surface candidate scholarship sources."""

    def __init__(self, db: AsyncSession | None = None, llm: AnthropicClient | None = None) -> None:
        self.db = db
        self.llm = llm if llm is not None else AnthropicClient()

    async def discover_new_sources(
        self,
        seed_url: str,
        max_links: int = 50,
        min_confidence: float = 0.5,
    ) -> list[DiscoveredSource]:
        outbound = await self._extract_outbound_links(seed_url, max_links=max_links)
        if not outbound:
            return []

        if not getattr(self.llm, "available", False):
            return self._heuristic_classify(outbound, min_confidence=min_confidence)

        try:
            payload = self.llm.call_json(
                system_prompt=_DISCOVERY_SYSTEM_PROMPT,
                user_prompt=self._build_user_prompt(outbound),
            )
        except Exception:
            return self._heuristic_classify(outbound, min_confidence=min_confidence)

        return self._payload_to_sources(payload, min_confidence=min_confidence)

    # ------------------------------------------------------------------
    # Link extraction
    # ------------------------------------------------------------------

    async def _extract_outbound_links(self, seed_url: str, max_links: int) -> list[dict[str, str]]:
        user_agent = "ScholarAI-Internal-Ingestion/0.1"
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(20.0), follow_redirects=True
            ) as client:
                response = await client.get(seed_url, headers={"User-Agent": user_agent})
        except (httpx.HTTPError, OSError):
            return []

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        seed_host = urlparse(seed_url).netloc
        seen: set[str] = set()
        out: list[dict[str, str]] = []

        for anchor in soup.find_all("a", href=True):
            if not isinstance(anchor, Tag):
                continue
            href = urljoin(seed_url, anchor["href"])
            host = urlparse(href).netloc
            if not host or host == seed_host:
                continue
            if href in seen:
                continue
            text = (anchor.get_text() or "").strip()
            haystack = (text + " " + href).lower()
            if not any(kw in haystack for kw in _SCOPE_KEYWORDS):
                continue
            seen.add(href)
            out.append({"url": href, "text": text})
            if len(out) >= max_links:
                break
        return out

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _build_user_prompt(self, links: list[dict[str, str]]) -> str:
        lines = [f"- {item['url']}  ({item['text']})" for item in links]
        return "Links to classify:\n" + "\n".join(lines)

    def _payload_to_sources(
        self,
        payload: dict[str, Any],
        min_confidence: float,
    ) -> list[DiscoveredSource]:
        out: list[DiscoveredSource] = []
        for candidate in payload.get("candidates", []):
            try:
                confidence = float(candidate.get("confidence", 0.0))
            except (TypeError, ValueError):
                continue
            if confidence < min_confidence:
                continue
            url = (candidate.get("url") or "").strip()
            if not url:
                continue
            country_code = (candidate.get("country_code") or "XX").upper()[:2]
            display_name = candidate.get("name") or self._fallback_name(url)
            out.append(
                DiscoveredSource(
                    base_url=url,
                    display_name=display_name,
                    country_code=country_code,
                    confidence=confidence,
                    source_key_suggestion=self._suggest_key(url, country_code),
                )
            )
        out.sort(key=lambda s: s.confidence, reverse=True)
        return out

    def _heuristic_classify(
        self,
        links: list[dict[str, str]],
        min_confidence: float,
    ) -> list[DiscoveredSource]:
        """Offline scoring when no LLM is configured.

        Rules tuned for the ScholarAI ingestion seed set:
        - ``.gov`` / ``.gov.<country>``  +0.30
        - ``.edu`` / ``.edu.<country>``  +0.25
        - ``.org``                       +0.10
        - scope keyword in anchor text   +0.20
        Base score 0.30; clamp to 0.95.
        """
        out: list[DiscoveredSource] = []
        for link in links:
            url = link["url"]
            text = link["text"]
            host = urlparse(url).netloc.lower()
            score = 0.30
            if host.endswith(".gov") or ".gov." in host:
                score += 0.30
            if host.endswith(".edu") or ".edu." in host:
                score += 0.25
            if host.endswith(".org"):
                score += 0.10
            if any(kw in text.lower() for kw in _SCOPE_KEYWORDS):
                score += 0.20
            score = min(score, 0.95)
            if score < min_confidence:
                continue
            base_url = f"{urlparse(url).scheme or 'https'}://{host}/"
            out.append(
                DiscoveredSource(
                    base_url=base_url,
                    display_name=text or self._fallback_name(url),
                    country_code="XX",
                    confidence=score,
                    source_key_suggestion=self._suggest_key(url, None),
                )
            )
        out.sort(key=lambda s: s.confidence, reverse=True)
        return out

    # ------------------------------------------------------------------
    # Naming helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_name(url: str) -> str:
        host = urlparse(url).netloc.replace("www.", "")
        first = host.split(".")[0]
        return first.title() if first else host

    @staticmethod
    def _suggest_key(url: str, country_code: str | None) -> str:
        host = urlparse(url).netloc.replace("www.", "")
        first = host.split(".")[0] or "source"
        suffix = (country_code or "xx").lower()
        return f"{first}-{suffix}"
