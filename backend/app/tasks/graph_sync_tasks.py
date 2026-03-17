import asyncio
from neo4j import GraphDatabase
from sqlalchemy import select
from app.core._celery import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import StudentProfile, Scholarship, RecordState

def _get_neo4j_driver():
    return GraphDatabase.driver(
        settings.NEO4J_URI, 
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )

@celery_app.task(name="sync_knowledge_graph", bind=True, max_retries=3)
def sync_knowledge_graph(self):
    """
    Celery task to synchronize PostgreSQL Student and Scholarship states into the Neo4j Knowledge Graph.
    Uses Cypher MERGE queries to maintain idempotency.
    """
    try:
        driver = _get_neo4j_driver()
        asyncio.run(_async_sync(driver))
        driver.close()
    except Exception as e:
        print(f"Graph Sync Pipeline Failed: {e}")
        self.retry(exc=e, countdown=60)

async def _async_sync(driver):
    async with SessionLocal() as db:
        # Load students
        profiles_result = await db.execute(select(StudentProfile))
        profiles = profiles_result.scalars().all()
        
        # Load scholarships
        scholarships_result = await db.execute(
            select(Scholarship).where(Scholarship.record_state.in_([RecordState.VALIDATED, RecordState.PUBLISHED]))
        )
        scholarships = scholarships_result.scalars().all()
        
        with driver.session() as session:
            for p in profiles:
                session.execute_write(_merge_student_tx, p)
            
            for s in scholarships:
                session.execute_write(_merge_scholarship_tx, s)

def _merge_student_tx(tx, profile):
    query = """
    MERGE (s:Student {id: $id})
    SET s.gpa_value = $gpa,
        s.target_degree_level = $degree,
        s.citizenship_country_code = $citizenship,
        s.target_country_code = $target_country
    """
    tx.run(query, 
        id=str(profile.id), 
        gpa=float(profile.gpa_value) if profile.gpa_value else None,
        degree=profile.target_degree_level.value if profile.target_degree_level else "MS",
        citizenship=profile.citizenship_country_code,
        target_country=profile.target_country_code
    )

def _merge_scholarship_tx(tx, scholarship):
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
    tx.run(query,
        id=str(scholarship.id),
        country=scholarship.country_code,
        gpa=float(scholarship.min_gpa_value) if scholarship.min_gpa_value else None,
        degrees=scholarship.degree_levels,
        citizenships=scholarship.citizenship_rules
    )
