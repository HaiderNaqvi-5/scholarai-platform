from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.recommendation_foundation_ping")
def recommendation_foundation_ping() -> dict[str, str]:
    return {
        "status": "ready",
        "message": "Celery foundation is active. Recommendation batch jobs remain deferred.",
    }
