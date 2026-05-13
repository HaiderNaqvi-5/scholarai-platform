# Progress — 2026-05-13 (session: test refactor for Pakistan PRD)

**Branch:** `feat/scraper-optimization`

## Tasks completed
- Ran backend pytest baseline. Initial transient cross-file failure on `test_b2b_share_persists_lead_with_snapshot` and two ingestion cache tests; both reproducibly resolved once the file state stabilised (242/242 unit, 50/50 integration on isolated runs).
- Audited the SCHOLARAI_PAKISTAN_PRD (sections 0, 0.5, 0.6, 1–10) against the existing backend test surface (`backend/tests/unit/*.py`, `backend/tests/integration/*.py`).
- Mapped every PRD acceptance bullet to an existing test. Coverage is already extensive: dedicated suites exist for plan guard, waitlist/pricing, CGPA conversion, Pakistan dataset, Pakistan recommendation matching, scholarship match service, tracker, SOP builder, visa interview, privacy/B2B, profile Pakistan fields, demo seed.
- Identified two real gaps and one drift:
  1. PRD §0.6 critical rule — "matching engine has ZERO imports from referral_enrollments/institutions tables" — had no automated guard.
  2. PRD §10 demo readiness — `backend/scripts/demo_seed_pakistan.py` was not pinned by any test, so the Zara Khan persona, plan=elite, 2099 expiry, and consent grants could regress silently.
  3. `tests/unit/test_privacy_and_b2b.py::_profile()` SimpleNamespace fixture was missing `gpa_scale` and the migration-0019 B2B fields that `services/privacy/b2b_share.py::_profile_snapshot` now reads — caused intermittent failure depending on file state.
- Filled the gaps:
  - Added `backend/tests/unit/test_b2b_trust_boundary.py` — AST-walks every module under `app/services/recommendations` and `app/services/scholarships` and asserts none of them reference `Institution`, `InstitutionStudent`, `ReferralEnrollment`, `UniversityLead`, or the equivalent table names. Two parametrized tests × two packages = 4 assertions.
  - Added `backend/tests/unit/test_demo_seed_pakistan.py` — 12 static checks on `scripts/demo_seed_pakistan.py` covering demo email, plan=elite, PKR currency, PK billing country, 2099 expiry, 5 consent grants, NUST persona, three-plan waitlist placeholders, scholarship/university/visa-question seed minimums (≥10, ≥30, ≥70 with required country splits), and a syntax-parse check.
  - Extended `_profile()` fixture in `tests/unit/test_privacy_and_b2b.py` with every field `_profile_snapshot` consumes (`gpa_scale`, `gmat_score`, `sat_score`, `budget_pkr_max`, `target_university_ids`, `current_university_id`, `hec_degree_level`, `intake_target`, `phone_e164`, `whatsapp_e164`, `current_employer`, `current_job_title`, `household_income_band`, `father_occupation`, `referral_source`, etc.) so the snapshot test is resilient to migration-0019 field additions.
- Re-ran the full backend suite: **306 passed, 0 failed**.

## Files touched
- `backend/tests/unit/test_b2b_trust_boundary.py` — NEW.
- `backend/tests/unit/test_demo_seed_pakistan.py` — NEW.
- `backend/tests/unit/test_privacy_and_b2b.py` — extended `_profile()` fixture with the B2B/Phase-C field surface.

## Open work / not in scope this session
- Frontend has no test surface (no `*.test.*` or `__tests__` under `frontend/src`). PRD §1–§10 frontend acceptance is currently only covered by the Playwright smoke suite at `tests/e2e/playwright/`. Adding component-level tests was de-scoped.
- Migration-0019 Pydantic schema tests (`gmat_score`, `sat_score`, `budget_pkr_max`, `target_university_ids`, `current_university_id`) — these fields are not on this branch's `app/schemas/student.py`, only on the b2b_share consumer side. When the schema branch merges, add round-trip tests under `tests/unit/test_profile_pakistan_fields.py`.

## Commands to resume
- `cd backend && python -m pytest tests/unit tests/integration -q`
- Selective: `python -m pytest tests/unit/test_b2b_trust_boundary.py tests/unit/test_demo_seed_pakistan.py -v`
- Live demo seed (requires running DB): `cd backend && python scripts/demo_seed_pakistan.py`
- API: `cd backend && python -m uvicorn app.main:app --reload`
- Frontend: `cd frontend && bun dev` (port 3001)
