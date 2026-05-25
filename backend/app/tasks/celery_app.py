from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

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
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "nightly-scholarship-ingestion": {
        "task": "tasks.run_nightly_ingestion",
        "schedule": crontab(hour=2, minute=0),
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
    # Ingestion freshness sentinel — runs every N minutes; emits Sentry +
    # admin-email when no nightly completion lands within INGESTION_STALE_HOURS.
    "ingestion-health-check": {
        "task": "tasks.run_ingestion_health_check",
        "schedule": crontab(minute=f"*/{settings.INGESTION_HEALTH_CHECK_INTERVAL_MINUTES}"),
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
