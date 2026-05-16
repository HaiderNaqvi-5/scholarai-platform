# progress.md — Q1 Retier · Task 17 (push-gate verification)

**Date:** 2026-05-16
**Branch:** `feat/pakistan-frontend-pass`
**Range:** `23942f5..27a57f2` (21 commits, Tasks 1–17)

## Tasks completed this session

The full Q1 retier landed across 21 commits on this branch:

| # | SHA | Task / Commit subject |
|---|-----|-----------------------|
| 1 | `23942f5` | feat(db): add scholarship.tier with premium backfill |
| 2 | `c7ce47e` | fix(db): correct scholarship backfill column names (title, provider_name) |
| 3 | `ba89ed6` | chore(db): make 20260516_0023 downgrade idempotent + docstring |
| 4 | `f307328` | feat(db): sop monthly usage + lifetime counter |
| 5 | `76c8e18` | feat(db): usage_ledger for burn-cap accounting |
| 6 | `b7bc088` | feat(models): scholarship tier + sop/usage ledger ORM |
| 7 | `24b57a8` | feat(plan_guard): Q1 retier caps + reveal gates |
| 8 | `de7f7b2` | feat(burn_cap): 60% per-tier accounting + LLM/WhatsApp cost helpers |
| 9 | `760ca39` | feat(match): internal buckets, Pro blur, Elite reveal |
| 10 | `b56ebd1` | feat(sop): per-plan monthly quota + free lifetime gate |
| 10b | `b56bd1f` | test(sop): align legacy sop_builder tests with new quota gate |
| 11 | `a510706` | feat(tracker): plan-aware cap (3/6/12) |
| 12 | `d0aa3d9` | feat(notifications): WhatsApp-only premium, drop SMS |
| 12b | `49495d9` | fix(reminders): adapt reminder_tasks to async fan_out_for_plan(db, user, message) |
| 13 | `e5ffe88` | feat(llm): burn-cap ledger wrapper + caller migration |
| 14 | `1d01c55` | feat(pricing): Q1 retier 2999/6000 + neutral bullets |
| 15 | `c50ad53` | feat(scholarships): premium tier paywall on public catalog |
| 16 | `f859091` | test(vocab): internal classification tokens must not leak |
| 17a | `79f8a7b` | feat(frontend): MatchCard + CompatibilityMeter + neutral copy |
| 17b | `27a57f2` | feat(upgrade): Q1 retier comparison rows |
| 17  | (this commit) | chore(q1-retier): push-gate run + progress.md + CLAUDE.md |

## Push-gate verification (Task 17)

All gates run from repo root on branch `feat/pakistan-frontend-pass`.

| Gate | Command | Result |
|------|---------|--------|
| Backend pytest (unit+integration) | `cd backend && pytest tests/unit tests/integration -q` | **444 passed, 1 xpassed**, 23 warnings, 66.46s |
| Compileall | `python -m compileall backend/app backend/tests` | **OK** (no errors) |
| KPI regression | `cd backend && pytest tests/unit/test_kpi_policy.py tests/unit/test_kpi_snapshot_service.py tests/unit/test_kpi_tasks.py tests/unit/test_health_kpi_alerts.py tests/integration/test_analytics_kpi_trends.py -q` | **13 passed**, 0.79s |
| Frontend lint | `cd frontend && bun run lint` | **exit 0** (no errors) |
| Frontend tsc | `cd frontend && bunx --bun tsc --noEmit` | **exit 0** (clean) |
| Frontend build | `cd frontend && bun run build` | **exit 0**, 31 routes generated |
| Docs governance | `python scripts/docs_governance_check.py` | **0 total failures** (terminology 0 / links 0 / canonical-tail 0) |
| Browser smoke (best-effort) | `python tests/e2e/playwright/run_smoke_suite.py` | 5 selector failures expected on greenfield branch — captured, not blocking (per push-gate policy) |
| Vocab guard re-run | `cd backend && pytest tests/unit/test_user_facing_vocab.py -v` | **6 passed, 1 xpassed** (matches Task 16 spec) |

No `test_kpi_regression.py` file exists in the suite; KPI regression was run as the union of all `*kpi*` tests in `backend/tests/`.

## Tasks in progress

None. Q1 retier closed.

## Open bugs / blockers

None new on Q1-retier-touched files. Pre-existing carry-over (untouched this session, not blocking push):

- Playwright smoke selectors stale on greenfield branch — 5 failing scripts: `public_scholarship_browse_smoke.py`, `seeded_recommendations_smoke.py`, `document_feedback_smoke.py`, `interview_practice_smoke.py`, `curation_smoke.py`. Per CLAUDE.md push-gate policy, browser smoke is relaxed on this branch until Frontend Pass S10.
- `.github/workflows/ci.yml` browser-smoke job still `continue-on-error`.
- Consent UI + cookie banner + settings privacy panel pending (S87 backlog).
- 23 deprecation warnings (pydantic `protected_namespaces`, `datetime.utcnow()` in `jose.jwt`, `bs4 _lxml strip_cdata`, `google._upb._message` PyType_Spec, one mis-marked asyncio test). Non-blocking.

## Files touched (Q1 retier 21 commits, range `23942f5..27a57f2`)

### Backend — DB / migrations
- `backend/alembic/versions/20260516_0023_scholarship_tier.py` (new — across 3 commits)
- `backend/alembic/versions/20260516_0024_sop_monthly_usage.py` (new)
- `backend/alembic/versions/20260516_0025_usage_ledger.py` (new)

### Backend — models / core / services
- `backend/app/models/__init__.py`, `backend/app/models/models.py` (scholarship tier + ORM for ledger tables)
- `backend/app/core/burn_cap.py` (new — 60% per-tier accounting + LLM/WhatsApp cost helpers)
- `backend/app/core/plan_guard.py` (caps + reveal gates)
- `backend/app/services/scholarships/match_service.py` (internal buckets, Pro blur, Elite reveal)
- `backend/app/services/documents/sop_builder.py` (monthly quota + lifetime gate + burn-cap wrapper)
- `backend/app/services/tracker/service.py` (plan-aware caps 3/6/12)
- `backend/app/services/notifications/__init__.py`, `services/notifications/channels.py` (WhatsApp-only premium, SMS dropped)
- `backend/app/services/llm/anthropic_client.py` (`complete_with_accounting`)
- `backend/app/services/visa_interview/evaluator.py`, `services/visa_interview/service.py` (burn-cap migration; `evaluate_answer` async)
- `backend/app/api/v1/routes/scholarships.py` (premium tier paywall on public catalog)
- `backend/app/api/v1/routes/waitlist.py` (Q1 pricing PKR 2,999 / 6,000)
- `backend/app/tasks/reminder_tasks.py`, `backend/app/tasks/alert_tasks.py` (WhatsApp-only fan-out)

### Backend — tests
- `backend/tests/unit/test_burn_cap.py` (new)
- `backend/tests/unit/test_burn_ledger_records.py` (new)
- `backend/tests/unit/test_plan_caps.py` (new)
- `backend/tests/unit/test_scholarship_match_service.py` (internal-bucket coverage)
- `backend/tests/unit/test_sop_quota.py` (new)
- `backend/tests/unit/test_sop_builder.py` (aligned to quota gate)
- `backend/tests/unit/test_tracker_service.py` (caps 3/6/12)
- `backend/tests/unit/test_alert_tasks.py`, `tests/unit/test_reminder_tasks.py` (WhatsApp-only)
- `backend/tests/unit/test_waitlist_and_pricing.py` (PKR 2,999 / 6,000)
- `backend/tests/unit/test_user_facing_vocab.py` (new — 6 pass + 1 xpass)
- `backend/tests/integration/test_public_scholarships.py` (premium paywall)

### Frontend
- `frontend/src/lib/api/types.ts` (Task 15 — neutral public match shape)
- `frontend/src/components/CompatibilityMeter.tsx` (new)
- `frontend/src/app/(student)/scholarships/page.tsx` (new — MatchCard + UnlockBlock)
- `frontend/src/components/scholarship/EligibilityMatrix.tsx` (aria-label sanitization)
- `frontend/src/app/upgrade/page.tsx` (Q1 pricing rows + `tier`→`plan` rename)

### Docs
- `CLAUDE.md` (Task 13 + 15 sections + Q1 retier closeout in this commit)

### Modified this commit only
- `progress.md` (this file)
- `CLAUDE.md` (Q1 retier closeout section)

## Commands to resume

```bash
# Bootstrap local DB / seeds
cd backend && python scripts/bootstrap_local.py

# Run API
cd backend && python -m uvicorn app.main:app --reload

# Run frontend
cd frontend && bun dev   # http://localhost:3000

# Re-run full backend suite
cd backend && pytest tests/unit tests/integration -q

# Re-run vocab guard specifically (expect 6 pass + 1 xpass)
cd backend && pytest tests/unit/test_user_facing_vocab.py -v

# Full push-gate before push
cd backend && pytest tests/unit tests/integration -q
python -m compileall backend/app backend/tests
cd frontend && bun run lint && bunx --bun tsc --noEmit && bun run build
python scripts/docs_governance_check.py
python tests/e2e/playwright/run_smoke_suite.py
```

## Verdict

**SHIPPABLE** — all hard gates green on the Q1 retier branch; smoke is relaxed per push-gate policy.
