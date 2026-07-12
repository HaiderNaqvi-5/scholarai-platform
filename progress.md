# progress.md — ScholarAI backend

**Date:** 2026-07-11
**Branch:** `fix/audit-2026-06-09-remediation` (HEAD `e01270a`, off `release/v1`)

## This session — Backend Audit Remediation Phases 7–10 (Tasks 24–42) COMPLETE

Executed the remaining 19 tasks of `docs/superpowers/plans/2026-06-09-backend-audit-remediation.md`
(Tasks 0–23 / P0, P1, P2-1…13,19 were already committed before this session). Subagent-driven:
one implementer + review per task, TDD (failing test → fix → verify → commit). 22 commits added.

**Test state:** baseline 637 passed → **673 passed, 7 skipped, 1 xfailed** (+36 tests, 0 regressions).
Single alembic head `20260609_0040`. `compileall` exit 0. `graph_sync` imports (P1-3 closed).
Final cross-task review: GO for merge.

### Finding → commit map (this session)
- P2-14 analytics typed body+response_model → `730d0c5`
- P2-15 documents upload/field caps (reused existing 255/12000/512KB/3 constants) → `12a04b1`
- P2-16 waitlist rate-limit+forbid-extra+upsert (email already unique, no migration) → `92eda6f`
- P2-17/18 eval requested-k + empty-gate; + route-aggregate vacuous-pass followup → `e68c7eb` + `fbb210a`
- folded-P2 LLM json-parse warn → `5d23870`
- folded-P2 export bundle reaper + beat → `7a80b8a` (amended to drop unrelated config removal)
- folded-P2 signup consent logging → `4612908`
- broken-#3 v2 alias isolation (middleware already scoped; added doc+test) → `4213ee1`
- P2-7 FK indexes (15) + migration `20260609_0039` → `5002570`
- P2-8 ReferralEnrollment.university_id FK + migration `20260609_0040` → `49927b0`
- P3 password_hash sentinel (NO-OP: clerk sync already sets `clerk:` sentinel; regression test) → `60e6e87`
- P3 local JWT → PyJWT with required claims (exception contract preserved) → `cd8ae6b` (amended to drop unrelated dep removals)
- P3 geo XFF gated on TRUSTED_PROXY_HOPS (routes/geo.py) → `382c3c1`
- P3 privacy ALLOWED_CONSENT_TYPES constant (drift found+fixed) → `4b6f430`
- P3 celery broker_connection_retry_on_startup + alembic id (id already canonical) → `4ece708`
- broken-#4 literal-before-param route ordering (interview/curation) → `b1f6d5f`
- health `/readyz` returns 503 on DB/Redis; probe Redis → `5c6fe03`
- CI runs all backend test dirs under Postgres → `d3d8d30`
- OpenAPI snapshot contract gate (missing D7) + 2 followups (CRLF + env-derived info.title) → `69956d4` + `495b910` + `e01270a`

## In-progress / next step
- **PR to `release/v1`** — branch pushed; open/merge PR with the finding→commit map above.
- After merge: run Postgres-gated migration round-trip (`alembic upgrade head && downgrade -2 && upgrade head`)
  on a live DB to exercise migrations `0039`/`0040` (skipped locally — `TEST_DATABASE_URL` unset).

## Open / not done (out of scope this session)
- Task 43 Step 6 (blocked audit item): `EXPLAIN ANALYZE` the pgvector retrieval path on a seeded live DB.
- Minor rollup (non-blocking, logged in `.superpowers/sdd/progress.md`): MAX_SUBMISSION_SCHOLARSHIP_IDS route/schema dup;
  schemas/privacy.py `_ALLOWED_CONSENT_TYPES` duplicate literal; DocumentService._store_uploaded_file unbounded read on non-route path.
- Latent: `verify_password` raises UnknownHashError on `clerk:` sentinel (clerk users 410 on local login → inert).

## Separate uncommitted effort (NOT part of this PR — left in working tree per user decision)
2026-07-09 ponytail-audit cleanup: ~45 staged deletions (`backend/legacy/`, `ai_services/`, `setup/`) + unstaged
`config.py`/`requirements.txt` dead-dep/config removals + Reticle frontend mods. Commits `7a80b8a`/`cd8ae6b` initially
swept some in; amended to keep them separate. Review/commit independently. Plan: `~/.claude/plans/hazy-brewing-hickey.md`.

## Resume commands
- Tests: `pytest backend/tests/unit backend/tests/integration -q`
- Compile: `python -m compileall backend/app backend/tests`
- Alembic head: `cd backend && python -m alembic heads` (expect single `20260609_0040`)
- Contract gate: `python -m pytest backend/tests/contract/test_openapi_snapshot.py -q`
- SDD ledger (per-task detail): `.superpowers/sdd/progress.md`
