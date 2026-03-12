"""
ScholarAI Data Pipeline
ETL utilities for processing scraped scholarship data
"""


def deduplicate_scholarships(scholarships: list, existing_hashes: set) -> list:
    """Remove duplicate scholarships based on source URL hash."""
    import hashlib
    unique = []
    for s in scholarships:
        url_hash = hashlib.md5(s.get("source_url", "").encode()).hexdigest()
        if url_hash not in existing_hashes:
            existing_hashes.add(url_hash)
            unique.append(s)
    return unique


def normalize_funding(amount: str) -> float:
    """Parse funding strings like '$10,000' or '€5000/month' to USD float."""
    import re
    if not amount:
        return 0.0
    cleaned = re.sub(r"[^0-9.]", "", str(amount))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def extract_fields_from_description(description: str) -> dict:
    """Use LLM to extract structured fields from raw scholarship description."""
    # TODO: integrate Gemini API for structured extraction
    return {
        "name": "",
        "country": "",
        "field_of_study": [],
        "degree_levels": [],
        "min_gpa": None,
        "funding_type": "",
        "deadline": None,
        "eligibility_criteria": {},
    }
