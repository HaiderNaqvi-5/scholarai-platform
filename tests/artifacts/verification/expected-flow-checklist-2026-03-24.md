# Expected Flow Checklist (2026-03-24)

Source docs reviewed:
- docs/scholarai/README.md
- docs/scholarai/02_prd_and_scope.md
- docs/scholarai/03_brand_and_design_system.md
- docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md
- docs/scholarai/INTERNAL_HANDOFF_PACKAGE.md

## 1) Login / Signup
- [ ] Signup page creates account successfully.
- [ ] Login page authenticates seeded/new users.
- [ ] Session persists across reloads.
- [ ] Protected routes require auth (redirect for unauthenticated users).
- [ ] Auth flow surfaces clear actionable errors.

## 2) Scholarships Browse / Detail
- [ ] `/scholarships` shows published records only.
- [ ] Search + filters work on MVP constrained corpus (Canada-first, MS scope).
- [ ] Browse supports calm, high-density scan (title, deadline, fit cues/state).
- [ ] Scholarship detail shows requirements, deadlines, funding, provenance, source link.
- [ ] Detail view distinguishes validated facts from guidance/explanations.

## 3) Recommendations
- [ ] User profile can be saved/loaded and used by recommendation flow.
- [ ] Hard eligibility constraints are applied before ranking.
- [ ] Recommendations return estimated fit (not deterministic acceptance claims).
- [ ] Rationale/explanations are visible and understandable.
- [ ] Save opportunity action works from recommendation context.

## 4) Dashboard
- [ ] `/dashboard` is protected and loads for authenticated users.
- [ ] Saved opportunities list is visible and stable.
- [ ] Dashboard provides clear entry points to profile/recommendations/prep tools.
- [ ] Empty states are honest and guide next action.

## 5) Documents
- [ ] Document (SOP/essay) submission succeeds.
- [ ] Feedback flow is bounded/advisory (not policy authority).
- [ ] Output separates: validated scholarship facts, retrieved guidance, generated guidance, limitations.
- [ ] Invalid scholarship-grounding identifiers fail with structured errors.

## 6) Interview
- [ ] Interview session creation supports practice mode (and optional scholarship targeting).
- [ ] User can submit at least one response in-session.
- [ ] Feedback is rubric-based and sectioned (not conversational clutter).
- [ ] Session summary/trend signals are available.
- [ ] Positioning remains advisory practice, not authoritative selection prediction.

## 7) Curation
- [ ] Curator workflow supports provenance lifecycle (`raw` -> `validated` -> `published`; internal docs also note `archived`).
- [ ] Raw records can be imported/ingested into curation intake.
- [ ] Review actions exist: edit/approve/reject/publish/unpublish.
- [ ] User-facing surfaces exclude non-published records.
- [ ] Provenance states are visually and semantically distinct.

## Demo acceptance sequence (expected)
- [ ] Browse published scholarships.
- [ ] Open scholarship detail.
- [ ] Sign up / log in.
- [ ] Open dashboard.
- [ ] Save profile, then open recommendations.
- [ ] Review rationale and save an opportunity.
- [ ] Submit document and review bounded feedback.
- [ ] Run interview practice response.
- [ ] (Optional internal) run curation review/publish lifecycle.
