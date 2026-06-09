import ssl

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings


def _rediss_ssl_options(url: str | None) -> dict | None:
    """SSL options for a ``rediss://`` Redis URL (e.g. Upstash).

    Celery's Redis result backend raises ``ValueError`` at worker boot if a
    ``rediss://`` URL has no ``ssl_cert_reqs``. Returns ``None`` for plain
    ``redis://``. ``CERT_REQUIRED`` validates the cert chain + hostname against
    the system trust store (Upstash uses publicly-trusted certs; the image
    ships ``ca-certificates``), so TLS is both encrypted and verified.
    """
    if url and url.startswith("rediss://"):
        return {"ssl_cert_reqs": ssl.CERT_REQUIRED}
    return None


celery_app = Celery(
    "scholarai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.recommendation_tasks",
        "app.tasks.scraper_tasks",
        "app.tasks.kpi_tasks",
        "app.tasks.alert_tasks",
        "app.tasks.reminder_tasks",
        "app.tasks.trial_tasks",
        "app.tasks.usage_ledger_tasks",
        "app.tasks.graph_sync_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
)

# Upstash exposes TLS-only ``rediss://`` endpoints; wire explicit SSL options so
# the worker/beat result backend boots instead of crashing on E_REDIS_SSL_CERT.
_broker_ssl = _rediss_ssl_options(settings.CELERY_BROKER_URL)
if _broker_ssl is not None:
    celery_app.conf.broker_use_ssl = _broker_ssl
_backend_ssl = _rediss_ssl_options(settings.CELERY_RESULT_BACKEND)
if _backend_ssl is not None:
    celery_app.conf.redis_backend_use_ssl = _backend_ssl

celery_app.conf.beat_schedule = {
    # Every-10-day cadence (1st / 11th / 21st @ 02:00 UTC).
    # Predictable calendar dates beat ``timedelta(days=10)`` — that anchor
    # would drift across beat restarts. 11-day gap from the 21st to the 1st
    # on 31-day months is acceptable. ``run_nightly_ingestion`` is the
    # back-compat alias that scraper_tasks.py exposes; the canonical task
    # name is ``tasks.run_scheduled_ingestion``.
    "scholarship-ingestion-decadal": {
        "task": "tasks.run_scheduled_ingestion",
        "schedule": crontab(hour=2, minute=0, day_of_month="1,11,21"),
    },
    # PRD §0.6 — Elite priority scholarship alerts (deadlines within 7 days).
    "priority-scholarship-alerts": {
        "task": "tasks.run_priority_scholarship_alerts",
        "schedule": crontab(hour=6, minute=7),
    },
    # PRD §0.6 / §0.5 — tracker deadline reminders with the free 30-day stop.
    "deadline-reminders": {
        "task": "tasks.run_deadline_reminders",
        "schedule": crontab(hour=6, minute=30),
    },
    # Q2-2026 Air University trial launch — daily 02:00 UTC (07:00 PKT)
    # downgrade of every user whose Pro trial has expired.
    "expire-trial-plans": {
        "task": "tasks.expire_trial_plans",
        "schedule": crontab(hour=2, minute=0),
    },
}

if settings.KPI_SNAPSHOT_RETENTION_ENABLED:
    celery_app.conf.beat_schedule["kpi-snapshot-retention-cleanup"] = {
        "task": "tasks.run_kpi_snapshot_retention_cleanup",
        "schedule": crontab(
            hour=settings.KPI_SNAPSHOT_RETENTION_CRON_HOUR,
            minute=settings.KPI_SNAPSHOT_RETENTION_CRON_MINUTE,
        ),
    }

if settings.USAGE_LEDGER_ROLLUP_ENABLED:
    celery_app.conf.beat_schedule["usage-ledger-rollup-prune"] = {
        "task": "tasks.run_usage_ledger_rollup",
        "schedule": crontab(
            hour=settings.USAGE_LEDGER_ROLLUP_CRON_HOUR,
            minute=settings.USAGE_LEDGER_ROLLUP_CRON_MINUTE,
        ),
    }
