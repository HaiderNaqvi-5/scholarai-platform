from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "scholarai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "run-scrapers-daily": {
            "task": "app.tasks.scraper.run_all_scrapers",
            "schedule": 86400.0,  # 24 hours
        },
    },
)
