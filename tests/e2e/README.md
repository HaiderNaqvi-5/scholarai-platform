# End-To-End Testing

This directory is reserved for MVP-critical browser and end-to-end test assets.

Initial browser test plan:
1. Landing page loads and shows ScholarAI branding.
2. Onboarding and profile routes resolve successfully.
3. Recommendations route resolves successfully.
4. Dashboard, document feedback, and interview routes resolve successfully.
5. A future profile submission flow navigates from profile to recommendations.
6. Login submits successfully and lands on the dashboard shell for an authenticated user.
7. Document feedback accepts a draft submission and renders the structured feedback panel.
8. Interview practice starts a session, accepts an answer, and renders rubric feedback.
9. Curator dashboard loads, shows raw records, and supports a basic approval action.
10. A new user can save a narrow profile and receive seeded published recommendations with explanation panels.
11. A full seeded demo rehearsal can move from signup to profile save to recommendations to saved opportunities on the dashboard.

Current note:
- The `webapp-testing` skill expects helper scripts such as `scripts/with_server.py`, but that helper is not present in this repo yet.
- Browser automation should therefore use direct Playwright scripts or add the helper later if the team standardizes on that workflow.
- Current smoke artifacts are `tests/e2e/playwright/auth_dashboard_smoke.py`, `tests/e2e/playwright/document_feedback_smoke.py`, `tests/e2e/playwright/interview_practice_smoke.py`, `tests/e2e/playwright/curation_smoke.py`, `tests/e2e/playwright/seeded_recommendations_smoke.py`, and `tests/e2e/playwright/rehearse_seeded_demo.py`.
- `tests/e2e/playwright/run_smoke_suite.py` runs the current smoke scripts independently and reports pass/fail per script so one broken path does not stop the whole walkthrough.
- All scripts assume local backend and frontend servers are already running.
- `curation_smoke.py` additionally assumes an admin user exists and at least one raw curation record is available.
- Local demo seeding now creates predictable accounts for browser demos:
  - student: `student@example.com` / `strongpass1`
  - admin: `admin@example.com` / `strongpass1`
- `seeded_recommendations_smoke.py` assumes the app can seed or already contains the demo scholarship dataset.
- `rehearse_seeded_demo.py` is the broader rehearsal path for the current recommendation demo.
- `backend/scripts/rehearse_seeded_demo.py` is the lighter API-level rehearsal path when browser tooling is unavailable.
