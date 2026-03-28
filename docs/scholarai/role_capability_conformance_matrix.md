# Role Capability Conformance Matrix

Use this matrix to track expected capability coverage by role and identify auth/scope mismatches.

| Role | Expected Capabilities | Endpoint/Domain Coverage | Evidence Links | Conformance Status | Mismatch Log |
| --- | --- | --- | --- | --- | --- |
| `student` | Browse, fit, save, prepare, track personal progress | `frontend/student/*`, `GET /scholarships`, `POST /shortlist`, `GET /progress` |  | `Planned` |  |
| `admin` | Data curation, moderation, operational controls, audit visibility | `frontend/admin/*`, `POST/PUT /scholarships`, `GET /admin/audit` |  | `Planned` |  |
| `owner` | Governance oversight, role policy control, stage conformance visibility | `frontend/owner/*`, `GET /owner/governance`, `POST /roles/*` |  | `Planned` |  |
| `mentor` | Advisory workflows, scoped student support, guidance artifacts | `frontend/mentor/*`, `GET /mentor/students`, `POST /mentor/advice` |  | `Planned` |  |
| `test-user` | Limited non-production validation flows with explicit constraints | `frontend/test/*`, sandbox-scoped API routes only |  | `Planned` |  |

## Conformance Status Values

- `Planned`
- `Conformant`
- `Partial`
- `Mismatch`

## Mismatch Logging Format

Record mismatches in the `Mismatch Log` cell using:

`[YYYY-MM-DD] <role> | expected=<capability> | observed=<behavior> | surface=<endpoint_or_screen> | severity=<low|med|high> | owner=<name_or_team> | target_fix=<issue_or_pr>`
