"""C2 — RSS/Atom feed parsing must be XXE / billion-laughs safe.

`_parse_feed` consumes XML from admin-registered (untrusted) external sources.
It must reject DTD/entity-based attacks (file disclosure, exponential entity
expansion) while still extracting links from well-formed feeds.
"""

import pytest

from app.services.ingestion.service import IngestionService


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code


def _patch_feed(monkeypatch, text: str) -> None:
    async def _fake_safe_get(url, **kwargs):
        return _FakeResponse(text)

    monkeypatch.setattr("app.services.ingestion.service.safe_get", _fake_safe_get)


BILLION_LAUGHS = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<rss><channel><item><link>&lol3;</link></item></channel></rss>
"""

XXE_FILE = """<?xml version="1.0"?>
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<rss><channel><item><link>http://evil.test/&xxe;</link></item></channel></rss>
"""

RSS_OK = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item><link>https://scholarships.test/a</link></item>
  <item><link>https://scholarships.test/b</link></item>
</channel></rss>
"""

ATOM_OK = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><link href="https://scholarships.test/x"/></entry>
  <entry><link href="https://scholarships.test/y"/></entry>
</feed>
"""


@pytest.mark.asyncio
async def test_parse_feed_blocks_billion_laughs(monkeypatch):
    _patch_feed(monkeypatch, BILLION_LAUGHS)
    svc = IngestionService(None)
    result = await svc._parse_feed("https://x.test/feed", lambda u: True, 50)
    assert result == set()


@pytest.mark.asyncio
async def test_parse_feed_blocks_external_entity_xxe(monkeypatch):
    _patch_feed(monkeypatch, XXE_FILE)
    svc = IngestionService(None)
    result = await svc._parse_feed("https://x.test/feed", lambda u: True, 50)
    assert result == set()


@pytest.mark.asyncio
async def test_parse_feed_extracts_rss_links(monkeypatch):
    _patch_feed(monkeypatch, RSS_OK)
    svc = IngestionService(None)
    result = await svc._parse_feed("https://x.test/feed", lambda u: True, 50)
    assert result == {"https://scholarships.test/a", "https://scholarships.test/b"}


@pytest.mark.asyncio
async def test_parse_feed_extracts_atom_links(monkeypatch):
    _patch_feed(monkeypatch, ATOM_OK)
    svc = IngestionService(None)
    result = await svc._parse_feed("https://x.test/feed", lambda u: True, 50)
    assert result == {"https://scholarships.test/x", "https://scholarships.test/y"}
