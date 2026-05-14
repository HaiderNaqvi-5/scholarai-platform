"""PR 3: DiscoveryService — LLM-classified new-source discovery from seed aggregator URLs."""

from __future__ import annotations

from typing import Any

import pytest


pytestmark = pytest.mark.asyncio


async def test_discover_new_sources_from_seed_homepage_via_llm(monkeypatch):
    """Crawl one level deep, classify outbound links via Claude, return high-confidence picks."""
    from app.services.ingestion.discovery import DiscoveryService, DiscoveredSource

    homepage_html = (
        "<html><body>"
        '<a href="https://chevening.org/">Chevening Scholarships</a>'
        '<a href="/contact-us">Contact</a>'
        '<a href="https://daad.de/scholarships/pakistan/">DAAD Pakistan Awards</a>'
        '<a href="https://random-blog.com/recipe">Recipe</a>'
        "</body></html>"
    )

    class FakeResp:
        status_code = 200
        text = homepage_html
        headers: dict[str, str] = {"content-type": "text/html"}

        def raise_for_status(self):
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, headers=None, **kw):
            return FakeResp()

    monkeypatch.setattr(
        "app.services.ingestion.discovery.httpx.AsyncClient",
        lambda **kw: FakeClient(),
    )

    fake_payload: dict[str, Any] = {
        "candidates": [
            {
                "url": "https://chevening.org/",
                "name": "Chevening Scholarships",
                "country_code": "GB",
                "confidence": 0.95,
            },
            {
                "url": "https://daad.de/scholarships/pakistan/",
                "name": "DAAD Pakistan Awards",
                "country_code": "DE",
                "confidence": 0.92,
            },
            {
                "url": "https://random-blog.com/recipe",
                "name": "Recipe Blog",
                "country_code": "XX",
                "confidence": 0.1,
            },
        ]
    }

    class FakeLLM:
        available = True

        def call_json(self, **kwargs):
            return fake_payload

    svc = DiscoveryService(db=None, llm=FakeLLM())  # type: ignore[arg-type]
    results = await svc.discover_new_sources(seed_url="https://studyabroad.gov.pk/")

    urls = [r.base_url for r in results]
    assert "https://chevening.org/" in urls
    assert "https://daad.de/scholarships/pakistan/" in urls
    # below min_confidence threshold should be dropped
    assert not any("recipe" in u for u in urls)
    # all returned candidates are DiscoveredSource dataclasses
    assert all(isinstance(r, DiscoveredSource) for r in results)
    assert all(r.confidence >= 0.5 for r in results)


async def test_discover_new_sources_falls_back_to_heuristics_offline(monkeypatch):
    """When LLM unavailable, TLD/keyword heuristic classification still surfaces candidates."""
    from app.services.ingestion.discovery import DiscoveryService

    homepage_html = (
        "<html><body>"
        '<a href="https://hec.gov.pk/awards/overseas">HEC Overseas Scholarship</a>'
        '<a href="https://example.edu/grants/phd">PhD Grant Award</a>'
        '<a href="https://blog.example.com/random-post">Random blog</a>'
        "</body></html>"
    )

    class FakeResp:
        status_code = 200
        text = homepage_html
        headers: dict[str, str] = {}

        def raise_for_status(self):
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, headers=None, **kw):
            return FakeResp()

    monkeypatch.setattr(
        "app.services.ingestion.discovery.httpx.AsyncClient",
        lambda **kw: FakeClient(),
    )

    class OfflineLLM:
        available = False

        def call_json(self, **kwargs):
            raise AssertionError("call_json should not be invoked when LLM is offline")

    svc = DiscoveryService(db=None, llm=OfflineLLM())  # type: ignore[arg-type]
    results = await svc.discover_new_sources(seed_url="https://studyabroad.gov.pk/")

    urls = [r.base_url for r in results]
    # .gov.pk + scholarship keyword → high heuristic score
    assert any("hec.gov.pk" in u for u in urls)
    # .edu + grant keyword → high heuristic score
    assert any("example.edu" in u for u in urls)
    # plain blog without keyword → filtered out at link-extraction step
    assert not any("blog.example.com" in u for u in urls)


async def test_discover_skips_links_without_scope_keywords(monkeypatch):
    """Links whose anchor text + URL lack scholarship keywords are dropped before LLM call."""
    from app.services.ingestion.discovery import DiscoveryService

    homepage_html = (
        "<html><body>"
        '<a href="https://acme.com/about">About Us</a>'
        '<a href="https://acme.com/team">Our team</a>'
        '<a href="https://www.weather.com/forecast">Weather forecast</a>'
        "</body></html>"
    )

    class FakeResp:
        status_code = 200
        text = homepage_html
        headers: dict[str, str] = {}

        def raise_for_status(self):
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, headers=None, **kw):
            return FakeResp()

    monkeypatch.setattr(
        "app.services.ingestion.discovery.httpx.AsyncClient",
        lambda **kw: FakeClient(),
    )

    class FakeLLM:
        available = True
        invocation_count = 0

        def call_json(self, **kwargs):
            type(self).invocation_count += 1
            return {"candidates": []}

    fake_llm = FakeLLM()
    svc = DiscoveryService(db=None, llm=fake_llm)  # type: ignore[arg-type]
    results = await svc.discover_new_sources(seed_url="https://studyabroad.gov.pk/")

    assert results == []
    # LLM must NOT be called when zero scope-matched links exist
    assert FakeLLM.invocation_count == 0
