# Shared Contracts

This directory is reserved for ScholarAI request/response contracts, stable type references, and future generated schemas if the team later needs cross-language sharing.

Current MVP stance:
- Frontend types may live locally in `frontend/src/lib/types.ts`.
- Backend Pydantic schemas remain authoritative for API contracts.
- Do not introduce code generation or schema sync tooling yet.
