# Backend Legacy Quarantine

This folder contains inactive backend routes and service files that are no longer part of the mounted ScholarAI MVP surface.

## Why these files were moved
- They were present on disk but not mounted in `backend/app/api/v1/__init__.py` or used by the active modular service packages.
- Leaving them inside the active app tree increased implementation drift and made it easy to reference stale contracts.
- They are preserved here for later extraction, archive, or selective refactor work.

## Current status
- `backend/app/api/v1/routes/` now reflects the active API surface only.
- `backend/app/services/` now reflects the active modular service packages only.
- Nothing in this folder should be treated as active MVP behavior unless it is explicitly moved back and rewired.
