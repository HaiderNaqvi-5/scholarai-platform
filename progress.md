# progress.md — handoff

**Date:** 2026-05-30
**Branch:** `chore/backend-eng-remediation` (rebased onto `s93/auth-tier-1` @ `ad14fef`)

## Session: backend engineering-standards remediation (Phase 0 + Phase 1)

Executed the first two phases of `docs/superpowers/plans/2026-05-29-backend-engineering-remediation.md`,
which closes the engineering-quality gaps (E1–E30) found in the 2026-05-29 backend audit
(distinct from the security audit in `security-audit.md`). Subagent-driven; every change verified
against a real Postgres test DB.

## Tasks completed this session (7 commits on top of `ad14fef`)
- **0.1 (E8)** `66c18fc` — split test-only deps (`pytest`, `pytest-asyncio`, `playwright`) into `backend/requirements-dev.txt`; CI test jobs install it.
- **0.2 (E30)** `fd37ae7` — `asyncio_mode=auto` in `pytest.ini`; removed blanket `pytestmark=pytest.mark.asyncio` from 16 files (kills the sync-test mis-mark warning).
- **0.3 (E6, keystone)** `5d9c38f` — Postgres-backed `db_session` + `app_client` fixtures in `tests/conftest.py` + `tests/integration/test_db_fixture_smoke.py`. Postgres-only; skip when `TEST_DATABASE_URL` unset.
- **0.4 (E6/E9)** `951ff5f` — new `backend-integration` CI job (pgvector/pg16 + redis); root `permissions: contents: read` + concurrency-cancel (closes sec-audit N34); pip caching.
- **0.5 (E9)** `982f7aa` — `pytest-cov` + `--cov-fail-under=72` on backend-sanity (measured 77%). `pytest.ini` untouched (floor lives in the CI command so the kpi-subset job is unaffected).
- **1.1 / E5 / E31** `f3512b9` — added the 5 `student_profiles` columns migration 0019 created but the ORM never declared (+ FK + indexes + CHECKs) → **data-loss footgun closed**; added `User.plan` CHECK; removed 2 duplicate kpi-snapshot indexes that broke `create_all`; dropped the test-side dedup workaround.
- **1.2 (E9)** `bd83122` — reconciled all remaining ORM↔DB drift (indexes, unique-constraint names, `universities` Numeric→Float to match deployed `double precision`); wired **`alembic check` as a blocking CI gate** in backend-integration.

## In-progress / next step
None mid-flight. Next planned task is **Task 1.3** (JSON→JSONB + missing indexes, E25/E26) — a real schema migration, not started.

## Open blockers / decisions needed
- **E32 (deferred):** turning on `compare_server_default=True` in `alembic/env.py` surfaces **38** server-default mismatches — the DB carries server-side defaults (`gen_random_uuid()` on ~10 UUID `id` cols, `'free'` on `users.plan`, booleans, `'{}'::jsonb` on `application_tracker_items.document_checklist` where the model's Python default is a populated 14-key dict). Needs a deliberate app-side-vs-DB-side default-strategy decision; left OFF (gate runs on `compare_type` only).
- **Phases 2–6 not started:** Phase 2 concurrency/perf (E1 sync Anthropic SDK on event loop, E2 inline SentenceTransformer encode, E3 DB pool unconfigured, E4 `/scholarships` in-memory filter, E19 export N+1) is the highest-value remaining work; then observability (E10–E12), architecture (E7/E13–E15), deps (E20–E23), API (E16/E17/E24), test depth (E29/E30/D7).

## Files touched
- `backend/requirements-dev.txt` (new), `backend/pytest.ini`
- `backend/tests/conftest.py`, `backend/tests/integration/test_db_fixture_smoke.py` (new)
- `backend/app/models/models.py`
- `.github/workflows/ci.yml`
- `CLAUDE.md`, `progress.md`, `docs/superpowers/plans/2026-05-29-backend-engineering-remediation.md` (new)

## Commands to resume / verify
```bash
# Real Postgres test DB (compose stack up; DB + vector ext already provisioned):
#   postgresql+asyncpg://scholarai:password@127.0.0.1:5432/scholarai_test

cd backend

# Full suite as CI runs it (no env -> db-smoke skips): expect 558 pass / 2 skip / 1 xfail, coverage >=72%
python -m pytest tests/unit tests/integration tests/integrations tests/api tests/core tests/db tests/services tests/scripts --cov=app --cov-fail-under=72 -q

# Drift gate (reset test DB first), expect "No new upgrade operations detected."
DATABASE_URL="postgresql+asyncpg://scholarai:password@127.0.0.1:5432/scholarai_test" alembic upgrade head
DATABASE_URL="postgresql+asyncpg://scholarai:password@127.0.0.1:5432/scholarai_test" alembic check

# DB-backed fixture smoke against real Postgres: expect 2 passed
TEST_DATABASE_URL="postgresql+asyncpg://scholarai:password@127.0.0.1:5432/scholarai_test" \
  python -m pytest tests/integration/test_db_fixture_smoke.py -q
```
