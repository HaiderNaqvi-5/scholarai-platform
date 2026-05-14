# Progress — 2026-05-14

**Branch:** `feat/phase-c-and-scraper-wip` (pushed to origin)

Branched off `feat/scraper-optimization` after Phase C re-verify on `feat/pakistan-pivot-merge`. Carries the Pakistan-pivot baseline plus four scraper-optimization PRs and the B2B Phase C handoff.

## Tasks completed this session

### Phase C — B2B data-capture, frontend edit surface + snapshot expansion
- `frontend/src/app/(student)/profile/page.tsx` (913 lines): 6-card rewrite — Contact / Academic / Tests / Goal / Aspirations / Background. Exposes all 25+ editable `StudentProfile` fields. `/api/v1/universities?country=<first target>` powers the shortlist picker. Optimistic save preserved. `bunx --bun tsc --noEmit` profile-clean (only pre-existing `EligibilityMatrix.tsx` drift remains, unrelated).
- `backend/app/services/privacy/b2b_share.py::_profile_snapshot`: extended to surface every new B2B field at share time. DPA + `b2b_share_consent` enforcement unchanged.
- `backend/tests/unit/test_privacy_and_b2b.py`: `_profile` SimpleNamespace fixture extended with all new snapshot fields. 14/14 tests green.

### Scraper optimization PRs (chained on top of `feat/scraper-optimization`)
- **`1bdde98` Conditional GET.** IngestionService stores per-source `ETag` / `Last-Modified`; subsequent fetches send `If-None-Match` / `If-Modified-Since`. `304 Not Modified` short-circuits — no parse, no LLM call, no DB write.
- **`457b047` Sitemap + RSS/Atom feed discovery.** New `source_feed` table (migration `20260514_0020_ingestion_caching.py`). IngestionService now resolves robots.txt → sitemap-index → URLs and parses RSS/Atom feeds before falling back to full-page scrape. Only newer-than-`last_seen_at` entries get fetched.
- **`fbdf473` DiscoveryService.** Crawl one level from a seed aggregator URL, keyword-filter outbound links, classify each candidate via Claude, return high-confidence `DiscoveredSource[]` for admin review. No auto-registration.
- **`5db76fb`** export `DiscoveryService` from `app/services/ingestion/__init__.py`.
- **`779490f` Tests + docs.** `test_ingestion_service` (ETag short-circuit + feed parsing), `test_discovery_service` (keyword filter + monkeypatched LLM classifier + confidence threshold), `test_b2b_trust_boundary` (PRD §0.6 enforcement: recommendation engine MUST NOT import from `university_leads` / `institutions`), `test_demo_seed_pakistan` (orchestrator coverage). Plus CLAUDE.md + this progress.md.

### Housekeeping
- `.gitignore`: `graphify-out/` (4.7M AST cache from the graphify skill) now excluded.
- `CLAUDE.md`: appended scraper-pass note + Phase C done note. 116 lines, under the 200-line cap.
- Earlier this session: branch confusion — `git checkout` mid-task from `feat/pakistan-pivot-merge` → `feat/scraper-optimization` made it look like edits had been reverted. They had only moved off the working tree. Re-verified Phase C work was already committed as `c096dc8` on `feat/pakistan-pivot-merge`.
- Pushed `feat/phase-c-and-scraper-wip` to `origin`. PR URL: `https://github.com/HaiderNaqvi-5/scholarai-platform/pull/new/feat/phase-c-and-scraper-wip`.

## Files touched this session
- `backend/alembic/versions/20260514_0020_ingestion_caching.py` — new (source_feed table + ETag/Last-Modified columns on source_registry).
- `backend/app/models/models.py` — `SourceFeed` ORM model + ETag/Last-Modified columns on `SourceRegistry`.
- `backend/app/models/__init__.py` — export `SourceFeed`.
- `backend/app/services/ingestion/__init__.py` — export `DiscoveryService`.
- `backend/app/services/ingestion/service.py` — conditional-GET, sitemap parsing, feed parsing.
- `backend/app/services/ingestion/discovery.py` — new module (233 lines).
- `backend/app/services/privacy/b2b_share.py` — extended `_profile_snapshot` (already on `feat/pakistan-pivot-merge` HEAD as part of `c096dc8`).
- `frontend/src/app/(student)/profile/page.tsx` — 6-card rewrite (same commit).
- `backend/tests/unit/test_ingestion_service.py` — ETag + feed tests (257 lines).
- `backend/tests/unit/test_discovery_service.py` — new (193 lines).
- `backend/tests/unit/test_b2b_trust_boundary.py` — new (92 lines).
- `backend/tests/unit/test_demo_seed_pakistan.py` — new (118 lines).
- `backend/tests/unit/test_privacy_and_b2b.py` — fixture extension.
- `.gitignore`, `CLAUDE.md`, `progress.md`.

## In-progress / next
- Open PR on GitHub for `feat/phase-c-and-scraper-wip` if user wants review. URL above.
- Apply migration `20260514_0020_ingestion_caching` against the live dev DB before exercising conditional GET / feed discovery end-to-end:
  `docker exec scholarai-platform-backend-1 alembic upgrade head`.
- Wire `/admin/sources` UI to surface `DiscoveryService` results for human approval. Currently the service is admin-callable but has no frontend route.
- Pre-existing `frontend/src/components/scholarship/EligibilityMatrix.tsx` drift still blocks a fully-green typecheck (19 errors, all in that one file: uses `profile.citizenship` / `degree_level` / `gpa` / `field_tags` / `language_scores` — none on current `StudentProfile`). Out of scope this session.
- Frontend container has no healthcheck (low priority; nothing depends on it).
- `broker_connection_retry_on_startup=True` deprecation in `app/tasks/celery_app.py` — still deferred per the "no cosmetic" rule.

## Open bugs / blockers
- None known. `/livez` 200; `/api/v1/universities` returns 30 rows for `country=GB` (401 without auth = correct).

## Commands to resume
- Stack: `cd scholarai-platform && docker compose up -d`
- Migrations: `docker exec scholarai-platform-backend-1 alembic upgrade head`
- Frontend dev: `cd scholarai-platform/frontend && bun dev` (port 3001)
- Backend reload after a code change: `docker cp <path> scholarai-platform-backend-1:/app/<same-path> && docker restart scholarai-platform-backend-1`
- Health: `curl http://localhost:8000/livez && curl http://localhost:8000/readyz`
- Tests:
  - `docker exec scholarai-platform-backend-1 pytest tests/unit/test_privacy_and_b2b.py -q`
  - `docker exec scholarai-platform-backend-1 pytest tests/unit/test_ingestion_service.py -q`
  - `docker exec scholarai-platform-backend-1 pytest tests/unit/test_discovery_service.py -q`
  - `docker exec scholarai-platform-backend-1 pytest tests/unit/test_b2b_trust_boundary.py -q`
  - `docker exec scholarai-platform-backend-1 pytest tests/unit/test_demo_seed_pakistan.py -q`
- Typecheck: `cd scholarai-platform/frontend && bunx --bun tsc --noEmit`
- Push gate (per `AGENTS.md`): backend unit+integration, KPI regression, frontend lint/typecheck/build, docs governance, browser smoke.
