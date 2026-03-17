from dataclasses import dataclass

from app.models import Scholarship, StudentProfile

MVP_FIELDS = {
    "data science",
    "ai",
    "artificial intelligence",
    "analytics",
    "business analytics",
    "machine learning",
}


@dataclass
class MatchEvaluation:
    score: float
    matched_criteria: list[str]
    constraint_notes: list[str]


def normalize_gpa(gpa_value: float | None, gpa_scale: float) -> float | None:
    if gpa_value is None or gpa_scale <= 0:
        return None
    return round((float(gpa_value) / float(gpa_scale)) * 4.0, 2)


def field_matches(target_field: str, field_tags: list[str]) -> bool:
    normalized_target = target_field.strip().lower()
    normalized_tags = {tag.strip().lower() for tag in field_tags if tag}

    if normalized_target in normalized_tags:
        return True

    if normalized_target in MVP_FIELDS:
        return bool(normalized_tags & MVP_FIELDS)

    return any(candidate in normalized_target for candidate in MVP_FIELDS) and bool(
        normalized_tags & MVP_FIELDS
    )


def scholarship_in_scope(scholarship: Scholarship) -> bool:
    if scholarship.country_code == "CA":
        return True

    if scholarship.country_code != "US":
        return False

    haystack = " ".join(
        [
            scholarship.title or "",
            scholarship.provider_name or "",
            scholarship.source_url or "",
        ]
    ).lower()
    return "fulbright" in haystack


def check_neo4j_eligibility(profile: StudentProfile, scholarship: Scholarship) -> bool:
    try:
        from app.core.config import settings
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
        
        query = """
        MATCH (s:Student {id: $student_id})
        MATCH (sch:Scholarship {id: $scholarship_id})
        
        WHERE (sch.min_gpa_value IS NULL OR s.gpa_value >= sch.min_gpa_value)
          AND (s.target_country_code = sch.country_code)
        
        MATCH (sch)-[:ACCEPTS_DEGREE]->(d:DegreeLevel {name: s.target_degree_level})
        MATCH (sch)-[:ACCEPTS_CITIZEN]->(c:Country {code: s.citizenship_country_code})
        
        RETURN count(sch) > 0 as is_eligible
        """
        
        with driver.session() as session:
            result = session.run(query, student_id=str(profile.id), scholarship_id=str(scholarship.id))
            record = result.single()
            if record and record["is_eligible"]:
                return True
            return False
            
    except Exception as e:
        print(f"Neo4j eligibility check failed or skipped: {e}")
        return True # Fallback to Python rules if graph is down


def evaluate_match(
    profile: StudentProfile,
    scholarship: Scholarship,
) -> MatchEvaluation | None:
    if scholarship.record_state.value != "published":
        return None

    # Stage 1: Graph-based constraint filtering
    if not check_neo4j_eligibility(profile, scholarship):
        return None

    if not scholarship_in_scope(scholarship):
        return None

    if scholarship.country_code != profile.target_country_code:
        return None

    scholarship_levels = {level.upper() for level in scholarship.degree_levels}
    if profile.target_degree_level.value not in scholarship_levels:
        return None

    if scholarship.citizenship_rules:
        normalized_rules = {rule.upper() for rule in scholarship.citizenship_rules}
        if profile.citizenship_country_code.upper() not in normalized_rules:
            return None

    matched_criteria: list[str] = []
    constraint_notes: list[str] = []
    score = 0.0

    score += 0.35
    matched_criteria.append(
        f"Study destination matches your target country choice: {scholarship.country_code}."
    )

    score += 0.25
    matched_criteria.append("The published record explicitly supports an MS-level applicant.")

    if field_matches(profile.target_field, scholarship.field_tags):
        score += 0.2
        matched_criteria.append(
            f"Field fit is aligned with the published tags: {', '.join(scholarship.field_tags[:3])}."
        )
    else:
        constraint_notes.append(
            "Field fit is broader than exact, so review the program emphasis before shortlisting."
        )

    normalized_gpa = normalize_gpa(profile.gpa_value, profile.gpa_scale)
    if scholarship.min_gpa_value is None:
        constraint_notes.append(
            "The published record does not list a GPA minimum, which lowers ranking confidence."
        )
    elif normalized_gpa is None:
        constraint_notes.append(
            "Your GPA was not provided, so the GPA portion of fit could not be fully evaluated."
        )
    elif normalized_gpa < float(scholarship.min_gpa_value):
        return None
    else:
        score += 0.2
        matched_criteria.append(
            f"Your normalized GPA clears the published minimum of {float(scholarship.min_gpa_value):.1f}."
        )

    if scholarship.country_code == "US":
        matched_criteria.append(
            "This US result remains in scope because the published source is Fulbright-related."
        )

    return MatchEvaluation(
        score=round(min(score, 0.99), 2),
        matched_criteria=matched_criteria,
        constraint_notes=constraint_notes,
    )
