"""Bulk approve + publish RAW ingested scholarships.

The ingestion pipeline lands records as RecordState.RAW. The catalog and
matching engine only see PUBLISHED. This walks RAW records and runs both
transitions per record:

    RAW --approve_record--> VALIDATED --publish_record--> PUBLISHED

via CurationService, committing per record so a mid-run failure is resumable.
An ADMIN/OWNER user is required as the curation actor.

Usage:
  cd backend
  python scripts/publish_ingested_scholarships.py --dry-run        # count only
  python scripts/publish_ingested_scholarships.py                  # publish all RAW
  python scripts/publish_ingested_scholarships.py --limit 150      # cap

NOTE: publish auto-indexes into OpenSearch (best-effort; failure is logged,
not fatal). Embeddings for matching are backfilled separately
(scripts/index_scholarships.py / the embedding-backfill job).
"""

import argparse
import asyncio
import os
import sys
import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models import RecordState, User, UserRole
from app.schemas.curation import CurationActionRequest
from app.services.curation.service import CurationService

ADMIN_ROLES = (UserRole.ADMIN, UserRole.OWNER, UserRole.DEV)
NOTE = "bulk publish via publish_ingested_scholarships.py"


async def _load_actor(session) -> User:
    result = await session.execute(
        select(User).where(User.role.in_(ADMIN_ROLES)).limit(1)
    )
    actor = result.scalar_one_or_none()
    if actor is None:
        raise SystemExit(
            "No ADMIN/OWNER/DEV user found. Seed one first "
            "(e.g. scripts/clerk_seed_demo.py or a demo seed) then retry."
        )
    return actor


async def run(dry_run: bool, limit: int | None) -> None:
    async with async_session_factory() as session:
        actor = await _load_actor(session)
        service = CurationService(session)

        items, total = await service.list_records(
            actor, state=RecordState.RAW.value, page=1, page_size=1
        )
        print(f"Actor: {actor.email} ({actor.role.value})")
        print(f"RAW records pending: {total}")
        if dry_run:
            print("--dry-run: no changes made.")
            return
        if total == 0:
            return

        published = 0
        failed = 0
        action = CurationActionRequest(note=NOTE)

        # Re-fetch page 1 each loop: approved/published rows leave the RAW
        # filter, so the queue shrinks until empty.
        while True:
            items, _ = await service.list_records(
                actor, state=RecordState.RAW.value, page=1, page_size=50
            )
            if not items:
                break
            for item in items:
                if limit is not None and published >= limit:
                    print(f"\nReached --limit {limit}.")
                    print(f"PUBLISHED={published}  FAILED={failed}")
                    return
                record_id = uuid.UUID(str(item.record_id))
                try:
                    await service.approve_record(record_id, action, actor)
                    await service.publish_record(record_id, action, actor)
                    await session.commit()
                    published += 1
                    print(f"  published {record_id} {item.title[:60]}")
                except Exception as exc:
                    await session.rollback()
                    failed += 1
                    print(f"  FAIL {record_id} {type(exc).__name__}: {exc}")
                    # Skip this record on next page fetch: archive so it leaves RAW.
                    try:
                        await service.reject_record(record_id, action, actor)
                        await session.commit()
                    except Exception:
                        await session.rollback()

        print(f"\nDONE  PUBLISHED={published}  FAILED(archived)={failed}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bulk publish RAW scholarships")
    parser.add_argument("--dry-run", action="store_true", help="count only, no writes")
    parser.add_argument("--limit", type=int, default=None, help="max records to publish")
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run, limit=args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
