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

celery_app.conf.beat_schedule = {
    "nightly-scholarship-ingestion": {
        "task": "tasks.run_nightly_ingestion",
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
