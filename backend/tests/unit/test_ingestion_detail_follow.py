"""Pin the contract that the ingestion parser, given a listing page
HTML, can produce candidates whose source_url points at the linked
detail page rather than the listing itself."""

from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.ingestion.service import IngestionService, CaptureResult


def _listing_html() -> str:
    return """
    <html><head>
        <title>UBC Awards Listing</title>
        <meta name='description' content='Awards in Data Science and Analytics for MS students.'/>
    </head><body>
        <ul>
          <li><a href='/awards/mds-excellence'>MDS Excellence Entrance Award</a></li>
          <li><a href='/awards/mds-international'>MDS International Scholarship</a></li>
          <li><a href='/about'>About</a></li>
        </ul>
    </body></html>
    """


def test_parser_emits_distinct_detail_urls():
    service = IngestionService(db=SimpleNamespace())
    source = SimpleNamespace(
        source_key="ubc_grad",
        display_name="UBC Graduate Awards",
        base_url="https://www.grad.ubc.ca",
        source_type="university",
    )
    capture = CaptureResult(
        html=_listing_html(),
        final_url="https://www.grad.ubc.ca/awards",
        title="UBC Awards Listing",
        capture_mode="httpx_fallback",
        metadata={},
    )

    candidates = service._parse_candidates(source, capture)

    award_urls = sorted(str(c.source_url) for c in candidates)
    assert "https://www.grad.ubc.ca/awards/mds-excellence" in award_urls
    assert "https://www.grad.ubc.ca/awards/mds-international" in award_urls
    # /about must not be picked up — does not match SCHOLARSHIP_KEYWORDS.
    assert all("/about" not in url for url in award_urls)
    # No two candidates may share a source_url.
    assert len(award_urls) == len(set(award_urls))


import pytest


@pytest.mark.asyncio
async def test_capture_follows_rel_next_up_to_depth(monkeypatch):
    """When the listing page declares <link rel='next' href='/awards?page=2'>,
    the capture chain must follow it once and merge candidates."""
    from app.services.ingestion import service as ing_service

    page1 = """
    <html><head>
        <title>Page 1</title>
        <link rel='next' href='/awards?page=2'/>
    </head><body>
        <a href='/awards/mds-excellence'>MDS Excellence Award</a>
    </body></html>
    """
    page2 = """
    <html><head><title>Page 2</title></head><body>
        <a href='/awards/mds-international'>MDS International Scholarship</a>
    </body></html>
    """

    captures = {
        "https://www.grad.ubc.ca/awards": page1,
        "https://www.grad.ubc.ca/awards?page=2": page2,
    }

    async def _fake_capture(self, url):
        return ing_service.CaptureResult(
            html=captures[url],
            final_url=url,
            title="t",
            capture_mode="test",
            metadata={"requested_url": url},
        )

    monkeypatch.setattr(ing_service.IngestionService, "_capture_source", _fake_capture)

    service = ing_service.IngestionService(db=None)
    multi = await service._capture_source_with_pagination(
        "https://www.grad.ubc.ca/awards",
        max_pages=3,
    )
    assert len(multi) == 2
    assert {m.final_url for m in multi} == set(captures.keys())
