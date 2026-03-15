# End-To-End Testing

This directory is reserved for MVP-critical browser and end-to-end test assets.

Initial browser test plan:
1. Landing page loads and shows ScholarAI branding.
2. Onboarding and profile routes resolve successfully.
3. Recommendations route resolves successfully.
4. Dashboard, document feedback, and interview routes resolve successfully.
5. A future profile submission flow navigates from profile to recommendations.

Current note:
- The `webapp-testing` skill expects helper scripts such as `scripts/with_server.py`, but that helper is not present in this repo yet.
- Browser automation should therefore use direct Playwright scripts or add the helper later if the team standardizes on that workflow.
