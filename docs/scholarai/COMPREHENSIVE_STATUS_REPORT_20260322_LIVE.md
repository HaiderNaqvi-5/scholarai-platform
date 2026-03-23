# ScholarAI Comprehensive Status Report (Live)

Date: 2026-03-22
Scope: Consolidated status from canonical docs + in-repo implementation state

## 1) MVP Status: done vs partial vs not done

### Done (implemented in current backend/code path)

- Core backend service structure and API routing are in place for `v1`, with active `v2` expansion and deprecation direction.
- Capability-first RBAC model is implemented, with role fallback compatibility window for migration safety.
- Institution-scope authorization checks are implemented in dependencies/guards.
- Recommendation/document/interview KPI snapshot capture is implemented.
- KPI trends/alerts are exposed through analytics and health surfaces.
- KPI policy version tracking is wired through relevant recommendation/document/interview flows.
- KPI snapshot retention cleanup is implemented (service purge methods + Celery task + beat schedule + config flags).
- CI now includes KPI regression protection.
- Tests exist for RBAC fallback/claims, KPI trends, KPI health alerts, and KPI retention cleanup paths.

### Partial (present but not at full target maturity)

- `/api/v2` parity is progressing, but not yet complete across all `v1` surfaces.
- Docs are partially updated for KPI maturity, but still lag in some files vs latest code changes.
- Operational runbooks/alert routing are partially present; external incident routing and escalation maturity remain incomplete.
- Demo readiness and public-live hardening have plans and audits, but full execution is still in progress.
- End-to-end production readiness (release gates, full observability dashboards, enforced SLO workflows) is partially complete.

### Not done (explicitly not complete yet)

- Full startup-scale feature set from roadmap docs (enterprise and growth tracks) is not implemented end-to-end.
- Complete v1 retirement is not done.
- Full production hardening checklist in docs is not fully closed.
- Several roadmap and research-track items remain design/spec level or deferred.

## 2) Deferred research (explicitly treated as non-MVP)

Based on research/roadmap docs, these remain deferred or exploratory tracks rather than MVP blockers:

- Advanced recommendation experimentation beyond baseline production policy logic.
- Higher-order explainability/reranking research variants and ablation-heavy evaluation tracks.
- Broader longitudinal learning science experiments (beyond current KPI instrumentation).
- Extended evaluation programs intended for publication-level rigor, not launch gating.
- Advanced model strategy work (future model variants, richer adaptation loops, and deeper experimentation pipelines).

## 3) Post-MVP / startup-scale features (explicit inventory)

The following are documented as post-MVP/startup-scale direction and are not fully implemented yet:

- Enterprise tenancy maturity (org-level governance depth, enterprise-grade controls expansion).
- Enterprise identity/connectivity expansions (beyond current baseline auth/RBAC migration path).
- Broader integration surface with external platforms and partner ecosystem workflows.
- Productization upgrades for scale operations (advanced ops dashboards, stronger incident automation, broader runbooks).
- Growth and monetization readiness tracks (commercial/scale operations beyond MVP baseline).
- Full public-live hardening completion across reliability, operations, and release processes.

## 4) Docs vs code reality: alignment and divergence

### Alignment

- Status docs that mark MVP as "not fully complete" align with current repo reality.
- RBAC capability-first migration direction in docs aligns with implementation now present in code.
- KPI maturity direction (instrumentation and health gating) aligns with current implementation trajectory.
- `v2` API direction and staged migration strategy align with active code changes.

### Divergence / drift

- Some docs under-report recent KPI maturity progress (retention cleanup, health alert surfacing, added tests).
- Some roadmap/readiness docs can read ahead of current operational closure state.
- Cross-doc consistency is uneven: status/audit/plan docs are not all synchronized to the same latest branch snapshot.

## 5) Practical "where we are now"

- ScholarAI is in a late-MVP hardening and migration stage, not a fully finished startup-scale state.
- Core backend foundations are strong and moving in the right direction.
- KPI and governance maturity are materially improved and actively tested.
- The biggest remaining gap is not "core missing backend" but "closure": parity completion, ops hardening, and doc synchronization.

## 6) Immediate next execution slices

1. Finalize `v2` parity map and publish explicit `v1` deprecation timeline.
2. Complete external alert routing + operational escalation runbooks.
3. Synchronize all status/audit docs to a single branch truth source.
4. Close remaining public-live hardening checklist items and rerun readiness audit.
