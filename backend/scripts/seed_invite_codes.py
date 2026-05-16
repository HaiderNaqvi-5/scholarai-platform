"""Seed the AIRU2026 invite code for the Air University exhibition launch.

Idempotent: if the row already exists the script prints its current state
(uses / max_uses / validity window) and exits without raising. Otherwise
it inserts the canonical configuration:

* Code: ``AIRU2026``
* Cohort: ``AU2026``
* Plan granted: ``pro``
* Per-user trial length: 30 days from redemption
* Max uses: 100 (bump on-spot at the booth via ``grant_invite_uses.py``)
* Window: 2026-05-19 09:00 PKT → 2026-05-26 23:59 PKT

Run against the Supabase **direct** connection (port 5432, not the
6543 pooler) so the INSERT runs in a normal transaction. Example:

    DATABASE_URL='postgresql+asyncpg://postgres:<pw>@db.<ref>.supabase.co:5432/postgres?sslmode=require' \\
        python scripts/seed_invite_codes.py
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.models import InviteCode  # noqa: E402


PKT = ZoneInfo("Asia/Karachi")
CODE = "AIRU2026"


async def main() -> int:
    valid_from = datetime(2026, 5, 19, 9, 0, 0, tzinfo=PKT)
    valid_until = datetime(2026, 5, 26, 23, 59, 59, tzinfo=PKT)

    async with async_session_factory() as db:
        existing = (
            await db.execute(select(InviteCode).where(InviteCode.code == CODE))
        ).scalar_one_or_none()

        if existing is not None:
            print(
                f"{CODE} already seeded: "
                f"uses={existing.uses}/{existing.max_uses}, "
                f"window={existing.valid_from.isoformat()} -> "
                f"{existing.valid_until.isoformat()}, "
                f"active={existing.is_active}"
            )
            return 0

        db.add(
            InviteCode(
                code=CODE,
                cohort="AU2026",
                grants_plan="pro",
                trial_days=30,
                max_uses=100,
                uses=0,
                valid_from=valid_from,
                valid_until=valid_until,
                is_active=True,
            )
        )
        await db.commit()
        print(
            f"Seeded {CODE}: 100 uses, valid "
            f"{valid_from.isoformat()} -> {valid_until.isoformat()}"
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
