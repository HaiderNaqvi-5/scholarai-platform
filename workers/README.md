# Workers

This directory is reserved for ScholarAI worker-specific entrypoints and operational notes.

Current MVP stance:
- Celery workers remain tied to the backend application code.
- This directory exists to prevent future worker logic from being mixed into unrelated app roots.
- No standalone worker implementation is introduced in this phase.
