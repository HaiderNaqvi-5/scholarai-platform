"""
Celery application configuration for ScholarAI.

Beat schedule:
  - recompute_all_scores: nightly at 02:00 UTC
  - full_scrape:          weekly Sunday at 03:00 UTC
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "scholarai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.recommendation_tasks",
        "app.tasks.scraper_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,          # don't ack until task completes
    worker_prefetch_multiplier=1,  # fair dispatch for long-running tasks
    task_default_queue="default",
    task_routes={
        "tasks.run_full_scrape":       {"queue": "scraper"},
        "tasks.compute_match_scores":  {"queue": "ml"},
        "tasks.recompute_all_scores":  {"queue": "ml"},
        "tasks.generate_sop":          {"queue": "ai"},
    },
    beat_schedule={
        "nightly-recompute-scores": {
            "task":     "tasks.recompute_all_scores",
            "schedule": "0 2 * * *",   # cron: 02:00 UTC daily
        },
        "weekly-scrape": {
            "task":     "tasks.run_full_scrape",
            "schedule": "0 3 * * 0",   # cron: Sunday 03:00 UTC
        },
    },
)
