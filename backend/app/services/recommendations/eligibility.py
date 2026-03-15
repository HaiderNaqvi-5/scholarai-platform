from app.models import Scholarship, StudentProfile

MVP_FIELDS = {
    "data science",
    "ai",
    "artificial intelligence",
    "analytics",
    "business analytics",
    "machine learning",
}


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


def evaluate_match(
    profile: StudentProfile,
    scholarship: Scholarship,
) -> tuple[float, list[str], list[str]] | None:
    if scholarship.record_state.value != "published":
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

    reasons: list[str] = []
    warnings: list[str] = []
    score = 0.0

    score += 0.35
    reasons.append(f"Target country aligns with {scholarship.country_code}.")

    score += 0.25
    reasons.append("Degree level matches the MVP MS track.")

    if field_matches(profile.target_field, scholarship.field_tags):
        score += 0.2
        reasons.append("Target field aligns with scholarship field tags.")
    else:
        warnings.append("Field alignment is broad rather than exact.")

    normalized_gpa = normalize_gpa(profile.gpa_value, profile.gpa_scale)
    if scholarship.min_gpa_value is None:
        warnings.append("Minimum GPA is not specified in the published record.")
    elif normalized_gpa is None:
        warnings.append("Profile GPA is missing, so GPA fit is not fully evaluated.")
    elif normalized_gpa < float(scholarship.min_gpa_value):
        return None
    else:
        score += 0.2
        reasons.append("Normalized GPA clears the published minimum.")

    return round(min(score, 0.99), 2), reasons, warnings
