# v0.1 Grounding/Citation Verification Evidence

Generated: 2026-03-28
Scope: `DocumentFeedback` grounding/citation upgrade hardening pass.

## Automated Gate Results

| Command | Result |
|---|---|
| `pytest backend/tests/integration/test_document_interview_policy_versions.py` | PASS |
| `pytest backend/tests/unit/test_document_service.py -k "citation or grounding or feedback"` | PASS |
| `npm run typecheck` | PASS |
| `npm run lint` | PASS |

## Payload Evidence Excerpts

### Grounded Draft (high-confidence path)

```json
{
  "summary": "The draft has a usable foundation and should next align its evidence more tightly with the validated scholarship context.",
  "grounding_score": 0.725,
  "coverage_flags": {
    "motivation": false,
    "preparation": true,
    "future_impact": true,
    "scholarship_fit": false
  },
  "ungrounded_warnings": [
    "The 'motivation' section is weak or missing and may reduce grounded quality.",
    "The 'scholarship fit' section is weak or missing and may reduce grounded quality.",
    "Scholarship grounding is provided, but the draft does not clearly connect to scholarship-specific fit."
  ],
  "citation_count": 2,
  "citations": [
    {
      "source_id": "<scholarship-uuid>",
      "title": "Ontario Graduate Scholarship",
      "url_or_ref": "https://example.org/ogs",
      "snippet": "Annual scholarship funding for graduate study.",
      "relevance_score": 0.95
    },
    {
      "source_id": "validated-facts",
      "title": "Validated scholarship facts",
      "url_or_ref": "grounded_context_sections.validated_facts",
      "snippet": "Derived from scholarship record fields used in this run.",
      "relevance_score": 0.8
    }
  ]
}
```

### Weak/Ungrounded Draft (fallback path)

```json
{
  "summary": "Needs more data: the draft is not yet grounded enough for reliable scholarship-specific guidance.",
  "grounding_score": 0.2375,
  "coverage_flags": {
    "motivation": false,
    "preparation": false,
    "future_impact": false,
    "scholarship_fit": true
  },
  "ungrounded_warnings": [
    "The 'motivation' section is weak or missing and may reduce grounded quality.",
    "The 'preparation' section is weak or missing and may reduce grounded quality.",
    "The 'future impact' section is weak or missing and may reduce grounded quality."
  ],
  "citation_count": 1,
  "citations": [
    {
      "source_id": "<scholarship-uuid>",
      "title": "Ontario Graduate Scholarship",
      "url_or_ref": "https://example.org/ogs",
      "snippet": "Annual scholarship funding for graduate study.",
      "relevance_score": 0.95
    }
  ]
}
```

## UI/Contract Proof References

- Integration contract assertion for citation object fields:
  - `backend/tests/integration/test_document_interview_policy_versions.py`
- Unit checks for fallback and legacy/structured citation metrics:
  - `backend/tests/unit/test_document_service.py`
- Document assistance UI support for coverage warning, inline markers, “Why this advice”, and citation list:
  - `frontend/src/components/documents/document-assistance-shell.tsx`
- Mentor dashboard citation count compatibility:
  - `frontend/src/components/mentor/mentor-dashboard-shell.tsx`

## Notes

- This artifact captures payload and code-level evidence for the grounding/citation stream.
- Dedicated desktop/mobile screenshot capture for this stream was not produced in this pass.
