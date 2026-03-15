from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.scraper_foundation_ping")
def scraper_foundation_ping() -> dict[str, str]:
    return {
        "status": "deferred",
        "message": "Broad scraping is intentionally not active in the foundation phase.",
    }
