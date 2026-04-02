import uuid
from datetime import UTC
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RecordState, Scholarship
from app.services.documents.guidance_assets import DOCUMENT_GUIDANCE_LIBRARY
from app.services.recommendations.eligibility import scholarship_in_scope

MAX_GROUNDED_SCHOLARSHIPS = 3


def _coerce_uuid(value: Any) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def normalize_grounding_ids(
    scholarship_id: Any | None = None,
    scholarship_ids: list[Any] | None = None,
) -> list[uuid.UUID]:
    raw_values: list[Any] = []
    if scholarship_id is not None:
        raw_values.append(scholarship_id)
    raw_values.extend(value for value in (scholarship_ids or []) if value not in (None, ""))

    normalized: list[uuid.UUID] = []
    invalid_values: list[str] = []
    seen: set[uuid.UUID] = set()
    for raw_value in raw_values:
        try:
            parsed = _coerce_uuid(raw_value)
        except (TypeError, ValueError):
            invalid_values.append(str(raw_value))
            continue
        if parsed in seen:
            continue
        seen.add(parsed)
        normalized.append(parsed)

    if invalid_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scholarship grounding IDs: {', '.join(invalid_values)}",
        )

    if len(normalized) > MAX_GROUNDED_SCHOLARSHIPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provide at most {MAX_GROUNDED_SCHOLARSHIPS} scholarship grounding IDs",
        )

    return normalized


async def validate_scholarship_grounding(
    db: AsyncSession,
    scholarship_id: Any | None = None,
    scholarship_ids: list[Any] | None = None,
) -> list[Scholarship]:
    normalized_ids = normalize_grounding_ids(scholarship_id, scholarship_ids)
    if not normalized_ids:
        return []

    result = await db.execute(
        select(Scholarship).where(Scholarship.id.in_(normalized_ids))
    )
    scholarships = result.scalars().all()
    scholarship_by_id = {scholarship.id: scholarship for scholarship in scholarships}

    missing_ids = [str(identifier) for identifier in normalized_ids if identifier not in scholarship_by_id]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scholarship grounding IDs were not found: {', '.join(missing_ids)}",
        )

    ordered_scholarships = [scholarship_by_id[identifier] for identifier in normalized_ids]
    violations: list[str] = []
    for scholarship in ordered_scholarships:
        if scholarship.record_state != RecordState.PUBLISHED:
            violations.append(
                f"{scholarship.id} is not published and cannot be used for grounded guidance"
            )
            continue
        in_scope, reason, _score = scholarship_in_scope(scholarship)
        if not in_scope:
            violations.append(f"{scholarship.id} is out of Phase 2 scope: {reason}")

    if violations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(violations),
        )

    return ordered_scholarships


def build_validated_facts(scholarships: list[Scholarship]) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    for scholarship in scholarships:
        base_fact = {
            "scholarship_id": str(scholarship.id),
            "scholarship_title": scholarship.title,
            "source_url": scholarship.source_url,
        }
        candidates = [
            ("Provider", scholarship.provider_name),
            ("Country", scholarship.country_code),
            ("Funding summary", scholarship.funding_summary),
            ("Funding type", scholarship.funding_type),
            ("Category", scholarship.category),
            ("Degree levels", ", ".join(scholarship.degree_levels[:3])),
            ("Field tags", ", ".join(scholarship.field_tags[:4])),
            (
                "Deadline",
                scholarship.deadline_at.astimezone(UTC).date().isoformat()
                if scholarship.deadline_at
                else None,
            ),
            (
                "Citizenship rules",
                ", ".join(scholarship.citizenship_rules[:4]) if scholarship.citizenship_rules else None,
            ),
            (
                "Minimum GPA",
                f"{float(scholarship.min_gpa_value):.2f}/4.0" if scholarship.min_gpa_value is not None else None,
            ),
        ]
        for label, value in candidates:
            if not value:
                continue
            facts.append(
                {
                    **base_fact,
                    "label": label,
                    "value": str(value),
                }
            )
    return facts[:12]


def retrieve_bounded_writing_guidance(
    document_type: str,
    scholarships: list[Scholarship],
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    keys_to_check = ["general", document_type.lower()]

    if scholarships:
        primary = scholarships[0]
        if primary.category:
            keys_to_check.append(f"category:{primary.category.lower()}")
        if primary.country_code:
            keys_to_check.append(f"country:{primary.country_code.upper()}")
        for level in primary.degree_levels[:2]:
            normalized_level = level.strip().upper()
            if normalized_level:
                keys_to_check.append(f"degree:{normalized_level}")
        for field_tag in primary.field_tags[:3]:
            normalized_field = field_tag.strip().lower().replace(" ", "-")
            if normalized_field:
                keys_to_check.append(f"field:{normalized_field}")

    seen: set[str] = set()
    for key in keys_to_check:
        for item in DOCUMENT_GUIDANCE_LIBRARY.get(key, []):
            if item["key"] in seen:
                continue
            seen.add(item["key"])
            selected.append(item)

    return selected[:10]


def flatten_grounded_context_sections(sections: dict[str, Any]) -> list[str]:
    flattened: list[str] = []
    for fact in sections.get("validated_facts", []):
        flattened.append(
            f"Validated fact: {fact.get('scholarship_title', 'Scholarship')} | "
            f"{fact.get('label', 'Fact')} = {fact.get('value', '')}"
        )
    for snippet in sections.get("retrieved_writing_guidance", []):
        flattened.append(f"Writing guidance: {snippet.get('snippet', '')}")
    for item in sections.get("generated_guidance", []):
        flattened.append(f"Generated guidance: {item.get('guidance', '')}")
    for limitation in sections.get("limitations", []):
        flattened.append(f"Limitation: {limitation}")
    return flattened


def build_scholarship_context_summary(scholarships: list[Scholarship]) -> str:
    lines: list[str] = []
    for scholarship in scholarships:
        parts = [
            scholarship.title,
            scholarship.provider_name,
            scholarship.country_code,
            scholarship.category,
            scholarship.funding_summary,
        ]
        line = " | ".join(part for part in parts if part)
        if scholarship.degree_levels:
            line = f"{line} | Degree levels: {', '.join(scholarship.degree_levels[:3])}"
        if scholarship.field_tags:
            line = f"{line} | Fields: {', '.join(scholarship.field_tags[:4])}"
        lines.append(line)
    return "\n".join(lines[:3])
