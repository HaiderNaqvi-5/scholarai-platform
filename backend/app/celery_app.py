"""
Celery application — root-level import used by workers.

Delegates all configuration to app.tasks.celery_app so that concrete
task modules and beat schedules are centralised in one place.
"""
from app.tasks.celery_app import celery_app  # noqa: F401 — re-export
