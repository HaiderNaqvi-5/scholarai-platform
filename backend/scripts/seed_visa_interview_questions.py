"""Seed the visa interview question bank (Feature 8, PRD §8).

Idempotent on (country, visa_type, question_text).

Usage:
    cd backend && python scripts/seed_visa_interview_questions.py
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
from app.demo.visa_questions import VISA_INTERVIEW_QUESTION_BANK  # noqa: E402
from app.models import VisaInterviewQuestion  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("seed_visa_interview_questions")


async def _seed() -> int:
    async with async_session_factory() as session:
        count = 0
        for payload in VISA_INTERVIEW_QUESTION_BANK:
            result = await session.execute(
                select(VisaInterviewQuestion).where(
                    VisaInterviewQuestion.country == payload["country"],
                    VisaInterviewQuestion.visa_type == payload["visa_type"],
                    VisaInterviewQuestion.question_text == payload["question_text"],
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                row = VisaInterviewQuestion(
                    country=payload["country"],
                    visa_type=payload["visa_type"],
                    question_text=payload["question_text"],
                )
                session.add(row)
            for key in ("category", "ideal_answer_notes", "difficulty"):
                setattr(row, key, payload.get(key))
            row.is_active = True
            count += 1
        await session.commit()
        return count


def main() -> int:
    seeded = asyncio.run(_seed())
    logger.info("Visa interview question bank seeded: %s rows.", seeded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
