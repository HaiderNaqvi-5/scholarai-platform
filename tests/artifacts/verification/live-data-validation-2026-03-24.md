# Live Data Validation Report (2026-03-24)

Generated: 2026-03-24T04:06:53.2465148Z

## Seeded/test accounts used
- student@example.com / strongpass1
- admin@example.com / strongpass1

## Validation matrix
| Area | Status | Evidence |
|---|---|---|
| Scholarships fetch + detail surface | PASS | list_count=4; all_published=True; detail_ok=True; detail_fields_ok=True; sample=Fulbright Foreign Student Program for Data and AI Study |
| Recommendations + explanation structure | PASS | profile_status=200; rec_count=3; explain_ok=True |
| Dashboard + saved opportunities behavior | PASS | saved_before=2; save_status=201; saved_after=3; auth_dashboard_smoke=manual-run |
| Document feedback response sections | BLOCKED | create=503; feedback=; sections_ok=False; invalid_status=400; invalid_structured=False |
| Interview session/feedback structure | BLOCKED | create=503; response=; structure_ok=False |
| Curation records/state transitions visibility | PASS | total=6; states=published, raw, validated; raw=200; validated=200; published=200; student_access=403 |

## Playwright smoke evidence (exit codes)
| Script | Exit |
|---|---:|
| public_scholarship_browse_smoke.py | 1 |
| seeded_recommendations_smoke.py | 1 |
| auth_dashboard_smoke.py | 1 |
| document_feedback_smoke.py | 1 |
| interview_practice_smoke.py | 1 |
| curation_smoke.py | 1 |
