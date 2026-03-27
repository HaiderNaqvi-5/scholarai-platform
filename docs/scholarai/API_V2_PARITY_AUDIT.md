# API v2 Parity Audit (Taskboard Subtask 06)

Date: 2026-03-23

## Purpose

Provide a current parity inventory between `/api/v1` and `/api/v2`, including explicit non-parity surfaces and next actions.

## Current Router Inventory

### v1 mounted surfaces

- `/api/v1/health`
- `/api/v1/auth`
- `/api/v1/profile` (+ `/api/v1/profiles` alias)
- `/api/v1/scholarships`
- `/api/v1/saved-opportunities`
- `/api/v1/recommendations`
- `/api/v1/documents`
- `/api/v1/interviews`
- `/api/v1/curation`
- `/api/v1/mentor` (+ `/api/v1/mentors` alias)
- `/api/v1/analytics`

### v2 mounted surfaces

- `/api/v2/recommendations`
- `/api/v2/documents`
- `/api/v2/interviews`
- `/api/v2/profile`
- `/api/v2/scholarships`
- `/api/v2/analytics`

## Parity Status

### Parity-present domains

- Recommendations
- Documents
- Interviews
- Profile
- Scholarships
- Analytics

### Non-parity (known intentional or pending)

- Health
- Auth
- Saved opportunities
- Curation
- Mentor

## Contract Header Behavior

- v1 responses carry:
  - `X-API-Contract-Version: v1`
  - Deprecation metadata when enabled (`Deprecation`, `Sunset`, `Link`, `X-API-V1-Sunset-Days`)
- v2 responses carry:
  - `X-API-Contract-Version: v2`
  - No deprecation headers

## Test Evidence Added

Integration tests now cover:

1. v1 deprecation headers + v2 version header behavior.
2. OpenAPI-based v2 route inventory snapshot to lock current parity and non-parity expectations.

Relevant test file:
- `backend/tests/integration/test_protected_routes.py`

## Next Actions (Owners)

1. **Auth parity decision** (Backend/Auth): decide whether to introduce `/api/v2/auth` or keep auth version-agnostic under policy exception.
2. **Curation parity plan** (Backend/Curation): determine migration window and admin-client impact.
3. **Saved opportunities parity** (Backend/Student domain): schedule endpoint migration for dashboard consumers.
4. **Mentor parity** (Backend/Mentor): align aliases and capability checks under v2 strategy.
5. **Health route strategy** (Platform): retain root health contract or add `/api/v2/health` with identical semantics.

