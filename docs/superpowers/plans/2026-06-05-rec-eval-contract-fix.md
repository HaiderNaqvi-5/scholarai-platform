# Rec-Eval Benchmark Contract Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the admin Recommendation-Evaluation page (`/admin/rec-eval`) render benchmark results instead of crashing, by correcting the frontend type + render to match the backend's nested response shape.

**Architecture:** Frontend-only, surgical, 2 source files. The backend `POST /recommendations/benchmarks/{id}/evaluate` returns a **nested** shape (`aggregate` object + `case_results[].metrics` as a list of metric objects). The frontend hand-declared a **flat** shape (`Record<string,number>` + top-level `pass_rate`) and calls `.toFixed()` on objects/arrays → `TypeError: v.toFixed is not a function` at render. We correct the inline TS type to the backend shape (source of truth), then rewrite the page's result block to consume it. The TypeScript compiler is used as the failing test: once the type is corrected, `tsc` flags every bad read in `page.tsx` (RED); rewriting the render makes `tsc` pass (GREEN).

**Tech Stack:** Next.js 16 / React 19 / TypeScript 5 / Tailwind 4 / Bun. No frontend unit-test infra exists (per `frontend/CLAUDE.md`), so verification = `tsc --noEmit` + `bun run build` + live browser drive via gstack `/browse`.

**Root-cause evidence (already gathered, do not re-investigate):**
- Backend response model: `backend/app/schemas/recommendations.py:229` `RecommendationBenchmarkEvaluationResponse` → `aggregate: RecommendationBenchmarkAggregate` (`:159`) with `pass_rate` + `average_metrics: list[RecommendationMetricItem]` + `gate_pass_rates: list[...]`; `case_results[].metrics: list[RecommendationMetricItem]` (`:154`).
- Route builds it: `backend/app/api/v1/routes/recommendations.py:401-410`.
- Frontend wrong type: `frontend/src/lib/api/endpoints/recommendations.ts:34-40` (flat).
- Frontend wrong reads: `frontend/src/app/(admin)/admin/rec-eval/page.tsx:94` (`result.pass_rate`), `:105` (`Object.entries(result.aggregate)…v.toFixed`), `:140` (`Object.values(c.metrics)…v.toFixed`).
- Auth is NOT the issue: `RecommendationEvaluationUser` (`dependencies.py:305`) accepts `RECOMMENDATION_EVALUATE` / `ADMIN_AUDIT_READ` / `OWNER_SYSTEM_READ`; ADMIN role holds the first two (`authorization.py:96`).
- Out of scope: `endpoints.recommendations.evaluate()` (`recommendations.ts:8-20`) is also drifted but has **zero callers** (grep-verified) — pre-existing dead code, leave untouched.

---

## File Structure

- **Modify** `frontend/src/lib/api/endpoints/recommendations.ts` — correct `evaluateBenchmark` return type to the nested backend shape. Add one shared `BenchmarkMetric` type alias (used by both `aggregate.average_metrics` and `case_results[].metrics`).
- **Modify** `frontend/src/app/(admin)/admin/rec-eval/page.tsx` — rewrite the result `<Card>` block (lines 88-153) to read `result.aggregate.pass_rate`, flatten `result.aggregate.average_metrics`, and flatten each `c.metrics`. Add a small `metricEntries()` helper. No other part of the page changes.
- No backend changes. No new files. No new dependencies.

---

## Task 1: Correct the frontend benchmark-evaluation type (RED)

**Files:**
- Modify: `frontend/src/lib/api/endpoints/recommendations.ts:34-40`

- [ ] **Step 1: Replace the `evaluateBenchmark` declaration with the nested shape**

Replace lines 34-40 (the current `evaluateBenchmark:` entry) with:

```ts
  evaluateBenchmark: (datasetId: string) =>
    api.post<{
      dataset_id: string;
      version: string;
      title: string;
      policy_version: string;
      metric_set: string;
      pipeline_version: string;
      case_results: {
        case_id: string;
        profile_label: string | null;
        metrics: BenchmarkMetric[];
        kpi_passed: boolean | null;
      }[];
      aggregate: {
        case_count: number;
        pass_count: number;
        pass_rate: number;
        average_metrics: BenchmarkMetric[];
        gate_pass_rates: { k: number; pass_rate: number }[];
      };
    }>(`/recommendations/benchmarks/${datasetId}/evaluate`),
```

- [ ] **Step 2: Add the shared `BenchmarkMetric` type alias**

Immediately below the existing `import` lines (after line 2), insert:

```ts
type BenchmarkMetric = {
  k: number;
  precision_at_k: number;
  recall_at_k: number;
  ndcg_at_k: number;
  mrr_at_k: number | null;
};
```

- [ ] **Step 3: Run the type-checker — expect it to FAIL (this is the reproduction)**

Run: `cd frontend && bunx --bun tsc --noEmit`
Expected: FAIL with errors in `src/app/(admin)/admin/rec-eval/page.tsx` — `Property 'pass_rate' does not exist` (page.tsx:94,95), and `.toFixed` / `Object.entries`/`Object.values` shape errors around `result.aggregate` (page.tsx:105-111) and `c.metrics` (page.tsx:126,140). These errors ARE the bug, now surfaced at compile time.

- [ ] **Step 4: Commit the corrected type**

```bash
cd frontend
git add src/lib/api/endpoints/recommendations.ts
git commit -m "fix(rec-eval): type evaluateBenchmark to backend nested shape"
```

---

## Task 2: Rewrite the result render to consume the nested shape (GREEN)

**Files:**
- Modify: `frontend/src/app/(admin)/admin/rec-eval/page.tsx`

- [ ] **Step 1: Add the `metricEntries` helper above the component**

Insert immediately after the `EvalResult` type alias (after page.tsx:14):

```tsx
function metricEntries(m: {
  k: number;
  precision_at_k: number;
  recall_at_k: number;
  ndcg_at_k: number;
  mrr_at_k: number | null;
}): [string, number][] {
  const entries: [string, number][] = [
    [`precision@${m.k}`, m.precision_at_k],
    [`recall@${m.k}`, m.recall_at_k],
    [`ndcg@${m.k}`, m.ndcg_at_k],
  ];
  if (m.mrr_at_k != null) entries.push([`mrr@${m.k}`, m.mrr_at_k]);
  return entries;
}
```

- [ ] **Step 2: Replace the result `<Card>` block (lines 88-153)**

Replace the entire `{result ? ( … ) : null}` block (page.tsx:88-153) with:

```tsx
      {result ? (
        <Card>
          <CardHeader>
            <CardTitle>Result · {result.dataset_id}</CardTitle>
            <CardDescription>
              Pass rate:{" "}
              <Badge tone={result.aggregate.pass_rate >= 0.8 ? "validated" : "caution"}>
                {Math.round(result.aggregate.pass_rate * 100)}%
              </Badge>{" "}
              · {result.aggregate.pass_count}/{result.aggregate.case_count} cases passed
            </CardDescription>
          </CardHeader>
          <CardBody className="space-y-4">
            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-ink-subtle">
                Aggregate (mean over cases)
              </p>
              <ul className="mt-2 grid gap-1 sm:grid-cols-2">
                {result.aggregate.average_metrics.flatMap(metricEntries).map(([label, v]) => (
                  <li
                    key={label}
                    className="flex items-center justify-between rounded-[8px] border border-[var(--color-border)] bg-paper-white px-3 py-1.5 font-mono text-sm"
                  >
                    <span className="text-ink-muted">{label}</span>
                    <span className="text-ink">{v.toFixed(3)}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-ink-subtle">
                Per-case ({result.case_results.length})
              </p>
              <div className="mt-2 max-h-96 overflow-auto rounded-[12px] border border-[var(--color-border)]">
                <table className="w-full text-sm">
                  <thead className="bg-paper-warm/40 text-left text-xs uppercase tracking-wider text-ink-subtle">
                    <tr>
                      <th className="px-3 py-2">Case</th>
                      {(result.case_results[0]?.metrics ?? [])
                        .flatMap(metricEntries)
                        .map(([label]) => (
                          <th key={label} className="px-3 py-2">
                            {label}
                          </th>
                        ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.case_results.map((c) => (
                      <tr
                        key={c.case_id}
                        className="border-t border-[var(--color-border)] hover:bg-paper-warm/30"
                      >
                        <td className="px-3 py-2 font-mono text-xs text-ink">{c.case_id}</td>
                        {c.metrics.flatMap(metricEntries).map(([label, v]) => (
                          <td key={label} className="px-3 py-2 font-mono text-ink">
                            {v.toFixed(3)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </CardBody>
        </Card>
      ) : null}
```

- [ ] **Step 3: Run the type-checker — expect PASS**

Run: `cd frontend && bunx --bun tsc --noEmit`
Expected: PASS (0 errors). The RED from Task 1 Step 3 is now resolved.

- [ ] **Step 4: Run lint + build — expect clean/green**

Run: `cd frontend && bun run lint && bun run build`
Expected: lint 0 errors; build green with the same route count as the current sprint baseline.

- [ ] **Step 5: Commit the render fix**

```bash
cd frontend
git add "src/app/(admin)/admin/rec-eval/page.tsx"
git commit -m "fix(rec-eval): render nested benchmark aggregate + per-case metrics"
```

---

## Task 3: Live browser verification (end-to-end)

**Prereq:** backend running (`docker compose up backend` or `cd backend && python -m uvicorn app.main:app --reload`) with the `v01_core_rank_quality` benchmark dataset present (`backend/app/data/recommendation_benchmarks/v01_core_rank_quality.json` — already committed). Frontend dev server on :3000 (`cd frontend && bun dev` — first `docker compose stop frontend` if the container holds the port, per `CLAUDE.md` port-conflict note).

- [ ] **Step 1: Drive the page via gstack `/browse`** (device rule §8: `/browse` for all web browsing; never `mcp__claude-in-chrome__*`)

1. Log in as `admin@example.com` / `strongpass1`.
2. Navigate to `/admin/rec-eval`.
3. Confirm the **Benchmark datasets** card lists `core_rank_quality` with case count + `k=…`.
4. Click **Evaluate** on that dataset.

- [ ] **Step 2: Assert the result renders (verifiable success criteria)**

- Toast shows `Benchmark complete.`
- **Result card stays mounted** (no error boundary / "Something went wrong on our side").
- Pass-rate badge shows a real percentage (e.g. `80%`), **not `NaN%`**.
- Aggregate list shows rows like `precision@1`, `recall@5`, `ndcg@10` with 3-decimal values.
- Per-case table shows one row per case with numeric cells.
- Browser console: **0 errors** (specifically no `v.toFixed is not a function`).

- [ ] **Step 3: Capture evidence**

Screenshot the rendered result card; note pass-rate %, case count, and console-clean status in the session log.

---

## Task 4: Docs + handoff (device session rules §1, §2)

**Files:**
- Modify: `scholarai-platform/CLAUDE.md`
- Modify/Create: `scholarai-platform/progress.md`

- [ ] **Step 1: Add a CLAUDE.md note** under the frontend contract-drift section (the "FIXED (2026-05-31) — contract crashes" cluster), recording: rec-eval benchmark page was the next instance of the hand-synced-type drift class; `evaluateBenchmark` type + result render corrected to backend nested shape; backend untouched; `endpoints.recommendations.evaluate()` flagged as drifted-but-dead (zero callers). Keep CLAUDE.md under 200 lines (trim per device rule if over budget).

- [ ] **Step 2: Update `progress.md`** with date + branch (`fix/rec-eval-contract`), task completed (rec-eval contract fix), files touched (the 2 frontend files), verification evidence (tsc/build/browser), and resume commands.

- [ ] **Step 3: Commit docs**

```bash
cd ..
git add CLAUDE.md progress.md
git commit -m "docs: record rec-eval benchmark contract fix"
```

---

## Verification Summary (Definition of Done)

1. `cd frontend && bunx --bun tsc --noEmit` → 0 errors.
2. `bun run lint` → 0 errors; `bun run build` → green.
3. `/admin/rec-eval` → click **Evaluate** → result card renders pass-rate %, aggregate rows, per-case table; **0 console errors**; no error boundary.
4. Backend diff = empty (`git -C backend status` shows no backend changes).
5. CLAUDE.md + progress.md updated.

## Notes / Assumptions

- **Assumption:** the live symptom is the evaluate-render crash. If, when driving the page, the **datasets list is empty** ("No datasets registered") instead, that is a *different* failure (benchmark-registry path / dataset not loaded) — stop and re-run systematic-debugging Phase 1 against `RecommendationBenchmarkRegistry` before proceeding. The list endpoint and evaluate endpoint are independent.
- **Pre-commit:** device rule §5 secret scan applies before every commit — these are UI/type-only edits, no env/secret surface, but run the scan anyway.
- **On push:** device rule §7 — refresh the graphify graph before any `git push`.
- **Branch:** do all work on `fix/rec-eval-contract` cut from the current frontend integration branch; do not commit to `main`/`master` directly.
