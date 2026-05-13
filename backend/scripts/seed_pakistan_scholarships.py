"""Seed Pakistan-specific scholarships into the local DB.

Idempotent: re-running upserts on (source_url) and keeps each row at
record_state=PUBLISHED so public browse picks them up immediately.

Usage:
    cd backend && python scripts/seed_pakistan_scholarships.py
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.demo.pakistan_dataset import (  # noqa: E402
    PAKISTAN_SCHOLARSHIP_SEED,
    PAKISTAN_SOURCE_REGISTRY_SEED,
)
from app.models import Scholarship, ScholarshipRequirement, SourceRegistry  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("seed_pakistan_scholarships")


async def _upsert_sources(session) -> dict[str, SourceRegistry]:
    by_key: dict[str, SourceRegistry] = {}
    for entry in PAKISTAN_SOURCE_REGISTRY_SEED:
        result = await session.execute(
            select(SourceRegistry).where(SourceRegistry.source_key == entry["source_key"])
        )
        source = result.scalar_one_or_none()
        if source is None:
            source = SourceRegistry(source_key=entry["source_key"])
            session.add(source)
        source.display_name = entry["display_name"]
        source.base_url = entry["base_url"]
        source.source_type = entry["source_type"]
        source.is_active = True
        by_key[entry["source_key"]] = source
    await session.flush()
    return by_key


async def _upsert_scholarship(session, payload: dict, sources: dict[str, SourceRegistry]) -> Scholarship:
    result = await session.execute(
        select(Scholarship)
        .where(Scholarship.source_url == payload["source_url"])
        .options(selectinload(Scholarship.requirements))
    )
    scholarship = result.scalar_one_or_none()
    if scholarship is None:
        scholarship = Scholarship(
            title=payload["title"],
            provider_name=payload["provider_name"],
            country_code=payload["country_code"],
            source_url=payload["source_url"],
            field_tags=[],
            degree_levels=[],
            citizenship_rules=[],
        )
        session.add(scholarship)

    scholarship.source_registry = sources[payload["source_key"]]
    scholarship.external_source_id = payload["external_source_id"]
    scholarship.title = payload["title"]
    scholarship.provider_name = payload["provider_name"]
    scholarship.country_code = payload["country_code"]
    scholarship.summary = payload["summary"]
    scholarship.funding_summary = payload["funding_summary"]
    scholarship.funding_type = payload.get("funding_type")
    scholarship.funding_amount_min = payload.get("funding_amount_min")
    scholarship.funding_amount_max = payload.get("funding_amount_max")
    scholarship.source_document_ref = payload["source_document_ref"]
    scholarship.field_tags = list(payload["field_tags"])
    scholarship.degree_levels = list(payload["degree_levels"])
    scholarship.citizenship_rules = list(payload["citizenship_rules"])
    scholarship.min_gpa_value = payload["min_gpa_value"]
    scholarship.deadline_at = payload["deadline_at"]
    scholarship.record_state = payload["record_state"]
    scholarship.imported_at = payload["imported_at"]
    scholarship.source_last_seen_at = payload["source_last_seen_at"]
    scholarship.review_notes = payload["review_notes"]
    scholarship.validated_at = payload["validated_at"]
    scholarship.published_at = payload["published_at"]
    scholarship.provenance_payload = dict(payload["provenance_payload"])
    scholarship.requirements = [
        ScholarshipRequirement(
            requirement_type=requirement["requirement_type"],
            operator=requirement["operator"],
            value_text=requirement.get("value_text"),
            value_json=requirement.get("value_json"),
        )
        for requirement in payload.get("requirements", [])
    ]
    return scholarship


async def _seed() -> tuple[int, int]:
    async with async_session_factory() as session:
        sources = await _upsert_sources(session)
        count = 0
        for payload in PAKISTAN_SCHOLARSHIP_SEED:
            await _upsert_scholarship(session, payload, sources)
            count += 1
        await session.commit()
        return len(sources), count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    sources, scholarships = asyncio.run(_seed())
    logger.info(
        "Pakistan dataset ready: %s sources, %s scholarships published.",
        sources,
        scholarships,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
