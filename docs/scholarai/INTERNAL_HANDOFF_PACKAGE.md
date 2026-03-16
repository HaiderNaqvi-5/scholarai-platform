# ScholarAI Internal Handoff Package

## Purpose
This note is for internal reviewers, supervisors, and developers who need a clear MVP handoff path without reading the full documentation pack first.

## What ScholarAI currently does
ScholarAI currently supports a narrow internal MVP flow built around published scholarship records and bounded preparation workflows.

Implemented product slices:
1. Public scholarship browse and scholarship detail pages over published records only.
2. Signup, login, session persistence, and protected workspace routes.
3. Student profile save/load flow.
4. Deterministic recommendation shortlist using seeded published records.
5. Saved opportunities and dashboard shell.
6. SOP or essay submission with bounded document feedback.
7. Interview practice sessions with rubric-based scoring.
8. Curator workflow for `raw`, `validated`, `published`, and `archived` scholarship states.
9. Manual raw-record import as the current upstream bridge into curation.

## Core demo flows
Recommended internal demo order:
1. Open `/scholarships` and show the published browse surface.
2. Open one scholarship detail page and explain that only published records are user-facing.
3. Sign up or log in.
4. Open `/dashboard` and show saved opportunities plus workflow entry points.
5. Open `/profile`, save a profile, and move into `/recommendations`.
6. Show recommendation rationale and save an opportunity.
7. Open `/document-feedback` and submit a short SOP or essay.
8. Open `/interview` and run one practice answer.
9. If showing internal admin tooling, open `/curation`, import a raw record, then explain the review and publish lifecycle.

## How to run it locally
### Fastest internal path
1. From the repository root, run `docker compose up --build`.
2. Wait for the backend bootstrap to apply Alembic migrations and seed demo data.
3. Open `http://localhost:3000`.
4. Verify `http://localhost:8000/health` returns a healthy response.

### Seeded demo accounts
- student login: `student@example.com` / `strongpass1`
- admin login: `admin@example.com` / `strongpass1`

These accounts are seeded only for local/internal demo workflows when demo seeding is enabled.

### Direct local path
1. Copy `backend/.env.example` to `backend/.env`.
2. Copy `frontend/.env.local.example` to `frontend/.env.local`.
3. Start PostgreSQL and Redis locally.
4. In `backend/`, install dependencies with `pip install -r requirements.txt`.
5. In `frontend/`, install dependencies with `npm ci`.
6. From `backend/`, run `python scripts/bootstrap_local.py`.
7. Start the backend with `uvicorn app.main:app --reload`.
8. Start the frontend with `npm run dev`.

### Important run note
If route files or other app-structure files changed after the frontend dev server started, restart the frontend process or rerun `docker compose up --build`. An already-running Next.js process can serve stale `404` responses for new routes.

## Reviewer navigation
Start here if you need the full context:
- Repo overview: `README.md`
- Documentation index: `docs/scholarai/README.md`
- Implementation status: `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`
- Demo audit: `docs/scholarai/DEMO_READINESS_AUDIT.md`

## Known limitations
1. The ingestion pipeline is not automated yet.
2. The scholarship browse surface is intentionally narrow and does not yet include broader filtering or richer search.
3. API contract normalization is improved but not fully complete across every endpoint.
4. Browser-level verification is still partly manual.
5. Only the first Alembic revision exists so far.

## What is not implemented yet
Still outside the current internal MVP readiness level:
1. Broad ingestion automation feeding raw scholarship records.
2. Advanced ML reranking or graph-aware recommendation infrastructure.
3. Full RAG-backed document assistance.
4. Adaptive conversational interview simulation.
5. Startup-scale admin analytics, partner workflows, or broad geography expansion.

## What to say during the demo when a slice is partial
Use direct, accurate phrasing:
- Scholarship discovery: "This is the MVP-safe browse surface over published records. Search depth and broader filtering are deferred."
- Recommendations: "These results are deterministic and rules-first. They explain fit using explicit constraints rather than a black-box model."
- Document feedback: "This is bounded writing guidance, not policy authority and not a full RAG system yet."
- Interview practice: "This is rubric-based practice scoring, not a conversational AI interviewer."
- Curation: "This shows the source-of-truth workflow. Automation into raw records is the next step, but the lifecycle enforcement is already in place."

## Internal deploy-readiness conclusion
ScholarAI is ready for an internal MVP handoff and a controlled internal demo if the team uses the documented bootstrap path, restarts stale local processes when needed, and stays within the bounded demo script above.

Verified in this pass:
1. `docker compose up --build -d frontend` successfully rebuilt the frontend service.
2. `http://localhost:8000/health` returned healthy.
3. `http://localhost:3000/scholarships` responded successfully after rebuild.
4. `tests/e2e/playwright/public_scholarship_browse_smoke.py` passed after rebuild.

## MVP decision
This handoff package is for internal deploy and presentation readiness only.

## Deferred items
- External-launch packaging.
- Heavy deployment infrastructure.
- Public-facing marketing or operational claims beyond the implemented slices.

## Assumptions
- Reviewers will use local or Docker Compose environments.
- Seeded demo data remains acceptable for internal presentation.
- The demo stays within the implemented flows described above.

## Risks
- A stale frontend dev process can hide newly added routes.
- Demo quality still depends on local rehearsal discipline.
- External presentation would still be premature without stronger automation and broader contract hardening.
