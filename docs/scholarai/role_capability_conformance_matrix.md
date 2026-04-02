# Role Capability Conformance Matrix

Use this matrix to track expected capability coverage by role and identify auth/scope mismatches.

| Role | Expected Capabilities | Endpoint/Domain Coverage | Evidence Links | Conformance Status | Mismatch Log |
| --- | --- | --- | --- | --- | --- |
| `student` | Browse, fit, save, prepare, track personal progress | `frontend/src/components/dashboard/dashboard-shell.tsx`, `GET /api/v1/scholarships`, `POST /api/v1/saved-opportunities`, `PATCH /api/v1/saved-opportunities/{id}/status` | `frontend/src/components/dashboard/dashboard-shell.tsx`, `backend/app/api/v1/routes/saved_opportunities.py` | `Conformant` |  |
| `admin` | Data curation, moderation, operational controls, audit visibility | `frontend/src/app/admin/page.tsx`, `GET /api/v1/analytics`, `frontend/src/app/curation/page.tsx` | `frontend/src/components/admin/analytics-dashboard-shell.tsx`, `backend/app/api/v1/routes/analytics.py` | `Conformant` |  |
| `owner` | Governance oversight, role policy control, stage conformance visibility | `frontend/src/app/owner/page.tsx`, `frontend/src/components/auth/owner-route.tsx`, `GET /api/v1/analytics`, `PATCH /api/v1/access-control/users/{id}/role`, `POST /api/v1/access-control/role-changes/{audit_id}/revert` | `frontend/src/components/owner/owner-dashboard-shell.tsx`, `backend/app/api/v1/routes/access_control.py`, `backend/tests/integration/test_access_control_routes.py` | `Conformant` |  |
| `mentor` | Advisory workflows, scoped student support, guidance artifacts | `frontend/src/app/mentor/page.tsx`, `GET /api/v1/mentor/pending-reviews`, `POST /api/v1/mentor/documents/{id}/feedback` | `frontend/src/components/mentor/mentor-dashboard-shell.tsx`, `backend/tests/integration/test_mentor_review_workflow.py` | `Conformant` |  |
| `test-user` | Limited non-production validation flows with explicit constraints | `frontend/src/components/dashboard/dashboard-shell.tsx`, constrained shortlist controls in browse/recommendations/detail | `frontend/src/components/dashboard/dashboard-shell.tsx`, `frontend/src/components/scholarships/scholarship-browse-shell.tsx`, `frontend/src/components/recommendations/recommendation-workspace.tsx` | `Conformant` |  |

## Conformance Status Values

- `Planned`
- `Conformant`
- `Partial`
- `Mismatch`

## Mismatch Logging Format

Record mismatches in the `Mismatch Log` cell using:

`[YYYY-MM-DD] <role> | expected=<capability> | observed=<behavior> | surface=<endpoint_or_screen> | severity=<low|med|high> | owner=<name_or_team> | target_fix=<issue_or_pr>`
