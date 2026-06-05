# progress.md — ScholarAI / AidwiseAI

**Date:** 2026-06-05
**Branch:** `fix/rec-eval-contract` (cut from `fix/backend-remediation`)

> Prior backend-remediation / perf-db handoff state is preserved in `CLAUDE.md` (perf-db-01..05, R7, AI-P2-05 sections).

## This session — /admin/rec-eval benchmark crash fixed (FE-only)

**Symptom:** admin Recommendation-Evaluation page → click **Evaluate** → brief "Benchmark complete." toast → page blanks to error boundary; pass-rate badge flashed `NaN%`.

**Root cause:** frontend/backend contract drift (same hand-synced-type class as the 2026-05-31 cluster, memory obs `7092`).
Backend `POST /recommendations/benchmarks/{id}/evaluate` (`response_model=RecommendationBenchmarkEvaluationResponse`, `schemas/recommendations.py:229`) returns a NESTED shape:
- `aggregate.{pass_rate, case_count, pass_count, average_metrics[], gate_pass_rates[]}`
- `case_results[].metrics[]` = list of `{k, precision_at_k, recall_at_k, ndcg_at_k, mrr_at_k}`

Frontend declared a FLAT type (`endpoints/recommendations.ts`) — top-level `pass_rate`, `aggregate`/`metrics` as `Record<string,number>` — and `rec-eval/page.tsx` called `.toFixed()` on those objects/arrays → `TypeError: v.toFixed is not a function`. TS missed it because the generic was hand-declared wrong.

**NOT the cause:** auth. `RecommendationEvaluationUser` (`dependencies.py:305`) accepts `RECOMMENDATION_EVALUATE` / `ADMIN_AUDIT_READ` / `OWNER_SYSTEM_READ`; ADMIN role holds the first two (`authorization.py:96`).

## Tasks completed
- [x] Diagnosis (systematic-debugging): root cause confirmed across auth + contract boundaries.
- [x] Plan: `docs/superpowers/plans/2026-06-05-rec-eval-contract-fix.md`.
- [x] **T1** corrected `evaluateBenchmark` FE type → backend nested shape (+`BenchmarkMetric` alias). Commit `8ca7106`. (Intentionally left tsc RED — 4 errors at page.tsx:94/95/111/142 = reproduction.)
- [x] **T2** rewrote result render with `metricEntries()` helper. Commit `39725fc`. tsc GREEN.
- [x] Two-stage subagent review APPROVED (spec: FE type matched backend Pydantic field-by-field; quality: keys unique, edge cases degrade gracefully).
- [x] Docs: CLAUDE.md note + this handoff.

## Files touched (this fix)
- `frontend/src/lib/api/endpoints/recommendations.ts` (type)
- `frontend/src/app/(admin)/admin/rec-eval/page.tsx` (render)
- `CLAUDE.md`, `progress.md`, `docs/superpowers/plans/2026-06-05-rec-eval-contract-fix.md`

## Verification
- `cd frontend && bunx --bun tsc --noEmit` → 0 errors
- `bun run lint` → 0; `bun run build` → green, 42 routes
- Backend NOT changed
- **Live click-through NOT exercised** — backend running in **Clerk auth mode** (local `/auth/login` → 410), no headless token. Render correctness is structural: `response_model=` makes FastAPI/Pydantic emit exactly the schema the FE type now mirrors.

## Open / next step
- **Optional live verify (operator):** `cd frontend && bun dev` (port 3000 free), sign in via Clerk hosted page as an admin, open `/admin/rec-eval`, click **Evaluate** on `core_rank_quality` → confirm result card renders real pass-rate %, aggregate rows, per-case table, 0 console errors.
- **Not pushed.** On push: device rule §5 secret scan (diff is UI/type-only, no secret surface) + §7 graphify `--update` before push completes.
- Pre-existing dead code (out of scope, noted only): `recommendations.evaluate()` (`/recommendations/evaluate`) type also drifted, **zero callers**.

## Resume commands
- Frontend: `cd frontend && bun dev` (http://localhost:3000) — `docker compose stop frontend` first if :3000 held.
- Typecheck/lint/build: `cd frontend && bunx --bun tsc --noEmit && bun run lint && bun run build`
- Backend (up this session): `docker compose up backend` or `cd backend && python -m uvicorn app.main:app --reload`
