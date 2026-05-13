"""Seed Pakistan-relevant universities into the universities table.

Idempotent on (name, country). Re-running updates the row in place.

Usage:
    cd backend && python scripts/seed_pakistan_universities.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.demo.pakistan_universities import UNIVERSITIES_SEED  # noqa: E402
from app.models import University  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("seed_pakistan_universities")


async def _seed() -> int:
    async with async_session_factory() as session:
        count = 0
        for payload in UNIVERSITIES_SEED:
            result = await session.execute(
                select(University).where(
                    University.name == payload["name"],
                    University.country == payload["country"],
                )
            )
            uni = result.scalar_one_or_none()
            if uni is None:
                uni = University(name=payload["name"], country=payload["country"])
                session.add(uni)
            for key, value in payload.items():
                setattr(uni, key, value)
            count += 1
        await session.commit()
        return count


def main() -> int:
    seeded = asyncio.run(_seed())
    logger.info("Pakistan universities ready: %s rows.", seeded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
