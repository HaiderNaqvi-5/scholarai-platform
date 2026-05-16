"""Admin: bump ``invite_codes.max_uses`` for an existing code on the spot.

Use at the booth when the printed flyer pool is exhausted but redemptions
are still flowing in. Reads + writes happen in a single transaction so
two concurrent operators can't double-bump.

Usage::

    DATABASE_URL='...' python scripts/grant_invite_uses.py AIRU2026 50

Exits non-zero if the code is unknown or the increment is non-positive,
so it composes cleanly with shell automation.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, update  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.models import InviteCode  # noqa: E402


async def bump(code: str, add: int) -> int:
    if add <= 0:
        print(f"ERROR: <add> must be > 0 (got {add})", file=sys.stderr)
        return 2

    async with async_session_factory() as db:
        row = (
            await db.execute(
                select(InviteCode).where(InviteCode.code == code).with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            print(f"ERROR: invite code not found: {code!r}", file=sys.stderr)
            return 1

        previous = row.max_uses
        await db.execute(
            update(InviteCode)
            .where(InviteCode.code == code)
            .values(max_uses=InviteCode.max_uses + add)
        )
        await db.commit()
        print(
            f"{code}: max_uses {previous} -> {previous + add} "
            f"(current uses: {row.uses})"
        )
        return 0


def _usage() -> None:
    print("Usage: python scripts/grant_invite_uses.py <CODE> <ADD>", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        _usage()
        raise SystemExit(64)
    try:
        increment = int(sys.argv[2])
    except ValueError:
        _usage()
        raise SystemExit(64) from None
    raise SystemExit(asyncio.run(bump(sys.argv[1].strip().upper(), increment)))
