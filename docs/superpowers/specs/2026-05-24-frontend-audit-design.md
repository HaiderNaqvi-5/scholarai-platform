# Frontend Full-Scale Audit — Design Spec

**Date:** 2026-05-24
**Branch:** master (audit is read-only; no source edits to `frontend/src`)
**Brand:** AidwiseAI (repo: scholarai-platform)
**Target:** http://localhost:3000 — Next.js 16.2 + React 19 + Tailwind 4
**Scope owner:** end-to-end frontend, landing through last feature

## 1. Goal

Produce `audit-out/AUDIT_REPORT_2026-05-24.md` containing:

1. Per-route findings table, 38 routes × 4 viewports × {visual, functional, a11y, copy}.
2. Each finding tagged P0/P1/P2/P3 + linked to `Front-upgrade.md` v4 section.
3. Prioritized fix backlog and recommended next-sprint slice (S90 scope).

Done = report exists, committed, reviewed by user.

## 2. Inputs

- Live dev server: `http://localhost:3000` (verified 200 at 1:59am 2026-05-24).
- Live backend: `http://localhost:8000/api/v1` (verified `/health` 200).
- Auth persona: `zara.khan@example.com` / `ScholarAI-Demo-2026!` (verified login 200, token 781 char).
- Existing audit harness: `frontend/scripts/audit/` (runner, routes manifest, auth, a11y axe, copy-grep, emoji-grep, state-mock, report).
- Spec source of truth: `Front-upgrade.md` v4 (2026-05-17, 2646 lines, §3.1 IA, §6 per-screen contracts, §7.5 banned-phrase ledger, §11.6 anti-slop).
- Repo CLAUDE.md, `frontend/CLAUDE.md` (S88–S89.2 history, anti-slop rules, design tokens).

## 3. Approach (Option A — hybrid)

Automated sweep handles mechanical checks (axe, screenshots, copy ledger, emoji). Manual review handles UX judgment (hierarchy, motion, copy intent, keyboard flow, error recovery, validated/AI partition discipline). Cheaper than pure manual, more accurate than pure static.

## 4. Phase plan

| Phase | Task | Estimate |
|-------|------|----------|
| P0 Setup | Extend `routes.mjs` (+10 routes: 6 admin, 2 mentor, 2 partners, dynamic IDs). Pick concrete IDs for `[id]` routes from zara data. | 30 min |
| P1 Automated | `bun run audit` full matrix; collect screenshots, axe JSON, copy hits. | 45–60 min wall |
| P2 Manual | Drive each of 38 routes through 4 viewports + exercise mutations + keyboard. Time budget per route in §6. | ~11 h |
| P3 Gap map | Cross-ref findings vs `Front-upgrade.md` v4 §3.1 / §6 / §7.5 / §11.6. Mark each "missing/partial/regression/polish". | 90 min |
| P4 Synthesis | Write `AUDIT_REPORT_2026-05-24.md` + `missing-vs-spec.md` + `sprint-slice-S90.md`. Commit. | 90 min |
| **Total** | | **~15 h** |

## 5. Deliverables

1. `audit-out/AUDIT_REPORT_2026-05-24.md` — executive findings + per-route + backlog.
2. `audit-out/screenshots/<route>__<viewport>__<state>.png` — evidence.
3. `audit-out/REPORT.md` — raw harness output.
4. `audit-out/missing-vs-spec.md` — gap map vs v4 spec.
5. `audit-out/sprint-slice-S90.md` — P0-only fix sprint scope.

## 6. Per-route time budget (P2 manual)

| # | Route | Auth | Estimate |
|---|-------|------|----------|
| 1 | `/` landing | public | 35 m |
| 2 | `/booth/air-university` | public | 20 m |
| 3 | `/upgrade` | public | 30 m |
| 4 | `/signup` + `?invite=AIRU2026` | public | 25 m |
| 5 | `/login` | public | 20 m |
| 6 | `/onboarding` | public | 30 m |
| 7 | `/universities` | public | 20 m |
| 8 | `/legal/[terms,privacy,dpa,cookie,refund]` ×5 | public | 25 m |
| 9 | System pages (not-found, error, global-error, offline, denied, maintenance) ×6 | public | 25 m |
| 10 | `/feed` | student | 35 m |
| 11 | `/discover` | student | 25 m |
| 12 | `/scholarships` (match) | student | 30 m |
| 13 | `/scholarships/[id]` | student | 30 m |
| 14 | `/saved` | student | 25 m |
| 15 | `/tracker` | student | 35 m |
| 16 | `/documents` | student | 25 m |
| 17 | `/documents/sop` | student | 35 m |
| 18 | `/documents/professor-email` | student | 25 m |
| 19 | `/documents/[id]` | student | 30 m |
| 20 | `/interviews` | student | 25 m |
| 21 | `/interviews/visa` | student | 30 m |
| 22 | `/interviews/[id]` | student | 30 m |
| 23 | `/profile` | student | 35 m |
| 24 | `/settings` | student | 30 m |
| 25 | `/admin` | admin | 20 m |
| 26 | `/admin/ingestion` + `[id]` | admin | 25 m |
| 27 | `/admin/curation` + `[id]` | admin | 30 m |
| 28 | `/admin/users` | admin | 20 m |
| 29 | `/admin/audit` | admin | 15 m |
| 30 | `/admin/rec-eval` | admin | 20 m |
| 31 | `/mentor/queue` | mentor | 20 m |
| 32 | `/mentor/documents/[id]` | mentor | 25 m |
| 33 | `/partners` + `/partners/universities` | partners | 20 m |
| **Sum** | | | **~660 min ≈ 11 h** |

## 7. Out of scope

- Security re-audit (S20 closed P0+P1 — see `SECURITY_AUDIT.md`).
- Backend changes.
- Lighthouse perf flamegraphs (visual LCP/INP smell only).
- i18n / translation.
- Source-code fixes — this pass is read-only diagnosis. Fix sprint = S90, separate plan.

## 8. Risks

- Zara real data thin: tracker=0, saved=1, docs=0, interviews list endpoint mismatch. Rely on harness state-mocks for "loaded"; note real-data limitation in report.
- Dynamic-ID routes need real IDs. P0 will pick from zara's saved scholarship + create stubs as needed via state-mock.
- `bun run audit` full matrix may exceed 60 min if many timeouts. Hard ceiling 90 min; degrade to per-route runs if needed.
- Harness manifest dated 5/18 — same day as S89.2. Validate during P0 that no S89.2 routes are stale-named.

## 9. Verification per phase (Karpathy goal-driven)

| Phase | Verification |
|-------|--------------|
| P0 | `bun run audit:self-test` passes; routes.mjs contains all 38 routes; zara token cached. |
| P1 | `audit-out/REPORT.md` exists; screenshot count = 38 routes × 4 viewports × n states ≥ 152 files. |
| P2 | Findings tracker has ≥1 entry per route (or "clean" marker). |
| P3 | Every finding tagged with v4 spec section ref. |
| P4 | Audit report + missing-vs-spec + S90-slice committed; user has read and approved. |

## 10. Anti-pattern guards (Karpathy)

- No "fix while you find" — diagnosis only. Resist refactor urge.
- No new abstractions in `scripts/audit/` beyond the +10 route entries.
- Every finding traces to either user-visible defect or v4 spec gap. No "this code style bothers me" entries.
- Plan changes during execution → write delta in `progress.md`, do not rewrite spec silently.
