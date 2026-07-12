"""Batch scholarship ingestion runner.

Runs ``tasks.run_source_ingestion`` once per source in ``SOURCES`` (inline,
no Celery broker/worker needed) and prints a per-source + total tally of
records found / created / skipped.

Records land as RecordState.RAW in the curation queue. Run
``publish_ingested_scholarships.py`` afterwards to take them live.

Prereqs:
  - Postgres up (DATABASE_URL) — migrations at head.
  - FIRECRAWL_API_KEY set (capture path is Firecrawl Cloud).
  - SSRF guard rejects private/loopback hosts; only public live URLs work.

Usage:
  cd backend
  python scripts/run_ingestion_batch.py
  python scripts/run_ingestion_batch.py --max-records 30

Tune MAX_RECORDS + SOURCES to hit your target count. Each source yields at
most MAX_RECORDS candidates (after dedup); listing/aggregator pages yield
many, single scholarship landing pages yield ~1.
"""

import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.tasks.scraper_tasks import run_source_ingestion

# Default cap per source. ~8 sources x 25 = up to 200 candidates pre-dedup,
# trimming toward the 100-150 target after fuzzy-dedup + 409 conflicts.
MAX_RECORDS = 25

# EDIT THIS LIST. Use DENSE LISTING / index pages (many scholarships per page).
# Homepages and single-scholarship landing pages yield ~0-1 usable rows and
# mostly nav-link noise (proven: a prior scrape of university homepages gave
# ~4% usable). These aggregator category pages enumerate many awards per page.
# Scraped rows still land RAW and need admin curation before publish.
# Public URLs only (SSRF guard blocks private/loopback hosts).
# (source_key, display_name, base_url, source_type)
SOURCES: list[tuple[str, str, str, str]] = [
    ("scholars4dev-pg",  "Scholars4Dev Postgraduate", "https://www.scholars4dev.com/category/level-of-study/postgraduate-scholarships/", "aggregator"),
    ("schol-pos-masters","Scholarship Positions MS",  "https://scholarship-positions.com/category/masters-scholarships/",     "aggregator"),
    ("opportunitydesk",  "Opportunity Desk",          "https://opportunitydesk.org/category/scholarships/",                   "aggregator"),
    ("scholarshipsads",  "ScholarshipsAds Masters",   "https://www.scholarshipsads.com/category/masters/",                    "aggregator"),
    ("findaphd-funding", "FindAPhD Funding",          "https://www.findaphd.com/phds/funding/",                               "aggregator"),
]


def _field(result, key: str, default=0):
    """Read a field from the task result, which may be a dict or an object."""
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch scholarship ingestion")
    parser.add_argument("--max-records", type=int, default=MAX_RECORDS)
    args = parser.parse_args()

    if not os.getenv("FIRECRAWL_API_KEY"):
        print("WARNING: FIRECRAWL_API_KEY not set — capture will fail. Set it and retry.")

    totals = {"found": 0, "created": 0, "skipped": 0, "failed_runs": 0}
    print(f"Running {len(SOURCES)} sources, max_records={args.max_records}\n")

    for source_key, display_name, base_url, source_type in SOURCES:
        try:
            result = run_source_ingestion(
                source_key=source_key,
                source_display_name=display_name,
                source_base_url=base_url,
                source_type=source_type,
                max_records=args.max_records,
            )
        except Exception as exc:  # network / SSRF reject / parse failure
            totals["failed_runs"] += 1
            print(f"  FAIL  {source_key:18s} {type(exc).__name__}: {exc}")
            continue

        found = _field(result, "records_found")
        created = _field(result, "records_created")
        skipped = _field(result, "records_skipped")
        status = _field(result, "status", "unknown")
        totals["found"] += found
        totals["created"] += created
        totals["skipped"] += skipped
        print(f"  {status:10s} {source_key:18s} found={found:3d} created={created:3d} skipped={skipped:3d}")

    print(
        f"\nTOTAL  found={totals['found']}  created(RAW)={totals['created']}  "
        f"skipped={totals['skipped']}  failed_runs={totals['failed_runs']}"
    )
    print("\nNext: python scripts/publish_ingested_scholarships.py --dry-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
