"""Seed initial legal documents v1.0 (Feature 9.5).

Idempotent on (slug, version). Re-running upserts body + sha256.
Flips older versions for the same slug to is_current=false.

Usage:
    cd backend && python scripts/seed_legal_documents.py
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, update  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.demo.legal_documents import LEGAL_DOCUMENTS_V1  # noqa: E402
from app.models import LegalDocument  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("seed_legal_documents")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def _seed() -> int:
    async with async_session_factory() as session:
        count = 0
        for payload in LEGAL_DOCUMENTS_V1:
            slug = payload["slug"]
            version = payload["version"]
            body = payload["body_markdown"]
            digest = _sha256(body)

            result = await session.execute(
                select(LegalDocument).where(
                    LegalDocument.slug == slug,
                    LegalDocument.version == version,
                )
            )
            doc = result.scalar_one_or_none()
            if doc is None:
                # Demote prior versions for this slug.
                await session.execute(
                    update(LegalDocument)
                    .where(LegalDocument.slug == slug, LegalDocument.is_current.is_(True))
                    .values(is_current=False)
                )
                doc = LegalDocument(slug=slug, version=version)
                session.add(doc)
            doc.body_markdown = body
            doc.sha256_hash = digest
            doc.is_current = True
            count += 1
        await session.commit()
        return count


def main() -> int:
    seeded = asyncio.run(_seed())
    logger.info("Legal documents seeded: %s rows.", seeded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
