"""Export-bundle disk reaper Celery beat task.

Mirrors ``kpi_tasks``/``usage_ledger_tasks`` shape: a config-gated helper
plus a thin ``@celery_app.task`` wrapper. Unlike those, the reaper
(``cleanup_expired_exports``) is pure filesystem cleanup against
``EXPORT_ROOT`` — no DB session is needed, so there's no async/db-session
wrapping to mirror. The download-time TTL check on
``DataExportRequest.expires_at`` is untouched.
"""
from __future__ import annotations

from app.core.config import settings
from app.services.privacy.export_service import cleanup_expired_exports
from app.tasks.celery_app import celery_app


def _run_export_cleanup() -> dict[str, int | bool]:
    if not settings.EXPORT_CLEANUP_ENABLED:
        return {"enabled": False, "bundles_removed": 0}
    removed = cleanup_expired_exports()
    return {"enabled": True, "bundles_removed": removed}


@celery_app.task(name="tasks.run_export_cleanup")
def run_export_cleanup() -> dict[str, int | bool]:
    return _run_export_cleanup()
