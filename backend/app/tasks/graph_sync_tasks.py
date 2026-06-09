"""Sync Postgres Student/Scholarship state into the Neo4j knowledge graph.

Idempotent Cypher MERGE. Uses the async Neo4j driver so it does not block the
event loop, and the async SQLAlchemy session factory. Retries only transient
Neo4j errors; programming errors fail fast (no blind 3x retry).
"""
from __future__ import annotations

import logging

import anyio
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, TransientError
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_factory
from app.models import RecordState, Scholarship, StudentProfile
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_async_neo4j_driver():
    return AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )


@celery_app.task(name="sync_knowledge_graph", bind=True, max_retries=3)
def sync_knowledge_graph(self):
    try:
        anyio.run(_async_sync)
    except (ServiceUnavailable, TransientError) as exc:
        logger.warning("graph_sync.transient_failure error=%s", exc)
        raise self.retry(exc=exc, countdown=60)
    except Exception:
        logger.exception("graph_sync.permanent_failure")
        raise  # do NOT retry programming errors


async def _async_sync() -> None:
    driver = _get_async_neo4j_driver()
    try:
        async with async_session_factory() as db:
            profiles = (await db.execute(select(StudentProfile))).scalars().all()
            scholarships = (
                await db.execute(
                    select(Scholarship).where(
                        Scholarship.record_state.in_(
                            [RecordState.VALIDATED, RecordState.PUBLISHED]
                        )
                    )
                )
            ).scalars().all()

        async with driver.session() as session:
            for profile in profiles:
                await session.execute_write(_merge_student_tx, profile)
            for scholarship in scholarships:
                await session.execute_write(_merge_scholarship_tx, scholarship)
    finally:
        await driver.close()


async def _merge_student_tx(tx, profile) -> None:
    query = """
    MERGE (s:Student {id: $id})
    SET s.gpa_value = $gpa,
        s.target_degree_level = $degree,
        s.citizenship_country_code = $citizenship,
        s.target_country_code = $target_country
    """
    await tx.run(
        query,
        id=str(profile.id),
        gpa=str(profile.gpa_value) if profile.gpa_value is not None else None,
        degree=profile.target_degree_level.value if profile.target_degree_level else "MS",
        citizenship=profile.citizenship_country_code,
        target_country=profile.target_country_code,
    )


async def _merge_scholarship_tx(tx, scholarship) -> None:
    query = """
    MERGE (sch:Scholarship {id: $id})
    SET sch.country_code = $country,
        sch.min_gpa_value = $gpa
    WITH sch
    UNWIND CASE WHEN size($degrees) > 0 THEN $degrees ELSE ['Unknown'] END as deg
    MERGE (d:DegreeLevel {name: deg})
    MERGE (sch)-[:ACCEPTS_DEGREE]->(d)
    WITH sch
    UNWIND CASE WHEN size($citizenships) > 0 THEN $citizenships ELSE ['Unknown'] END as cit
    MERGE (c:Country {code: cit})
    MERGE (sch)-[:ACCEPTS_CITIZEN]->(c)
    """
    await tx.run(
        query,
        id=str(scholarship.id),
        country=scholarship.country_code,
        gpa=str(scholarship.min_gpa_value) if scholarship.min_gpa_value is not None else None,
        degrees=list(scholarship.degree_levels or []),
        citizenships=list(scholarship.citizenship_rules or []),
    )
