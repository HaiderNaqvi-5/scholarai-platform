from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.models import Scholarship, StudentProfile

MVP_FIELDS = {
    "data science",
    "ai",
    "artificial intelligence",
    "analytics",
    "business analytics",
    "machine learning",
}


@dataclass(frozen=True)
class EligibilityRuleResult:
    key: str
    label: str
    status: str
    hard: bool
    student_value: str | None
    scholarship_value: str | None
    score: float
    reason: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "status": self.status,
            "hard": self.hard,
            "student_value": self.student_value,
            "scholarship_value": self.scholarship_value,
            "score": round(self.score, 4),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class EligibilityGraphNode:
    id: str
    type: str
    label: str
    metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EligibilityGraphEdge:
    source: str
    target: str
    relation: str
    status: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass
class MatchEvaluation:
    score: float
    matched_criteria: list[str]
    constraint_notes: list[str]
    passed_rule_count: int
    total_rule_count: int
    field_alignment: float
    country_alignment: float
    gpa_alignment: float
    deadline_urgency: float
    rule_results: list[EligibilityRuleResult]
    eligibility_graph: dict[str, Any]


def normalize_gpa(gpa_value: float | None, gpa_scale: float) -> float | None:
    if gpa_value is None or gpa_scale <= 0:
        return None
    return round((float(gpa_value) / float(gpa_scale)) * 4.0, 2)


def field_matches(target_field: str, field_tags: list[str]) -> bool:
    return field_alignment_score(target_field, field_tags) >= 0.7


def field_alignment_score(target_field: str, field_tags: list[str]) -> float:
    normalized_target = _normalize_text(target_field)
    normalized_tags = [_normalize_text(tag) for tag in field_tags if tag]
    if not normalized_target or not normalized_tags:
        return 0.0

    tag_set = set(normalized_tags)
    if normalized_target in tag_set:
        return 1.0

    target_tokens = _tokenize(normalized_target)
    best_overlap = 0.0
    for tag in tag_set:
        tag_tokens = _tokenize(tag)
        shared = target_tokens & tag_tokens
        if not shared:
            continue
        overlap = (2 * len(shared)) / max(len(target_tokens) + len(tag_tokens), 1)
        best_overlap = max(best_overlap, overlap)

    if normalized_target in MVP_FIELDS and tag_set & MVP_FIELDS:
        best_overlap = max(best_overlap, 0.85)
    elif any(seed in normalized_target for seed in MVP_FIELDS) and tag_set & MVP_FIELDS:
        best_overlap = max(best_overlap, 0.72)

    return round(min(best_overlap, 1.0), 4)


def scholarship_in_scope(scholarship: Scholarship) -> tuple[bool, str, float]:
    haystack = " ".join(
        [
            scholarship.title or "",
            scholarship.provider_name or "",
            scholarship.source_url or "",
            scholarship.summary or "",
        ]
    ).lower()

    if "daad" in haystack:
        return False, "DAAD records remain deferred in Phase 1.", 0.0

    if scholarship.country_code == "CA":
        return True, "Canada remains the primary recommendation market in Phase 1.", 1.0

    if scholarship.country_code == "US" and "fulbright" in haystack:
        return True, "US scope is limited to Fulbright-adjacent records while Canada stays first.", 0.82

    return False, "Phase 1 scope keeps non-Canada records deferred unless they are Fulbright-related.", 0.0


def deadline_urgency_score(deadline_at: datetime | None, *, now: datetime | None = None) -> float:
    if deadline_at is None:
        return 0.45

    current_time = now or datetime.now(UTC)
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=UTC)

    days_until_deadline = (deadline_at - current_time).total_seconds() / 86400
    if days_until_deadline < 0:
        return 0.0
    if days_until_deadline <= 14:
        return 1.0
    if days_until_deadline <= 45:
        return 0.85
    if days_until_deadline <= 90:
        return 0.65
    if days_until_deadline <= 180:
        return 0.45
    return 0.3


def evaluate_match(
    profile: StudentProfile,
    scholarship: Scholarship,
) -> MatchEvaluation | None:
    rule_results: list[EligibilityRuleResult] = []
    matched_criteria: list[str] = []
    constraint_notes: list[str] = []

    published = getattr(scholarship.record_state, "value", scholarship.record_state) == "published"
    rule_results.append(
        EligibilityRuleResult(
            key="published",
            label="Published record",
            status="pass" if published else "fail",
            hard=True,
            student_value=None,
            scholarship_value=str(getattr(scholarship.record_state, "value", scholarship.record_state)),
            score=1.0 if published else 0.0,
            reason="Only published scholarships can be recommended.",
        )
    )
    if not published:
        return None

    scope_allowed, scope_reason, country_alignment = scholarship_in_scope(scholarship)
    rule_results.append(
        EligibilityRuleResult(
            key="phase_scope",
            label="Phase 1 market scope",
            status="pass" if scope_allowed else "fail",
            hard=True,
            student_value=profile.target_country_code.upper(),
            scholarship_value=scholarship.country_code.upper(),
            score=country_alignment,
            reason=scope_reason,
        )
    )
    if not scope_allowed:
        return None
    matched_criteria.append(scope_reason)

    country_matches = scholarship.country_code.upper() == profile.target_country_code.upper()
    rule_results.append(
        EligibilityRuleResult(
            key="country_target",
            label="Target country alignment",
            status="pass" if country_matches else "fail",
            hard=True,
            student_value=profile.target_country_code.upper(),
            scholarship_value=scholarship.country_code.upper(),
            score=country_alignment if country_matches else 0.0,
            reason="Published destination matches the student's current target country."
            if country_matches
            else "Published destination does not match the student's current target country.",
        )
    )
    if not country_matches:
        return None
    matched_criteria.append(
        f"Study destination matches your target country choice: {scholarship.country_code.upper()}."
    )

    scholarship_levels = {str(level).upper() for level in scholarship.degree_levels}
    target_degree = profile.target_degree_level.value.upper()
    degree_matches = target_degree in scholarship_levels
    rule_results.append(
        EligibilityRuleResult(
            key="degree_level",
            label="Degree level eligibility",
            status="pass" if degree_matches else "fail",
            hard=True,
            student_value=target_degree,
            scholarship_value=", ".join(sorted(scholarship_levels)) or None,
            score=1.0 if degree_matches else 0.0,
            reason="Published degree levels include the student's target degree."
            if degree_matches
            else "Published degree levels exclude the student's target degree.",
        )
    )
    if not degree_matches:
        return None
    matched_criteria.append(
        f"The published record supports your target degree level: {profile.target_degree_level.value.upper()}."
    )

    citizenship_rules = {rule.upper() for rule in scholarship.citizenship_rules if rule}
    citizenship_code = profile.citizenship_country_code.upper()
    citizenship_matches = not citizenship_rules or citizenship_code in citizenship_rules
    rule_results.append(
        EligibilityRuleResult(
            key="citizenship",
            label="Citizenship rule",
            status="pass" if citizenship_matches else "fail",
            hard=True,
            student_value=citizenship_code,
            scholarship_value=", ".join(sorted(citizenship_rules)) or "open",
            score=1.0 if citizenship_matches else 0.0,
            reason="Citizenship rules allow this applicant."
            if citizenship_matches
            else "Citizenship rules currently exclude this applicant.",
        )
    )
    if not citizenship_matches:
        return None
    if citizenship_rules:
        matched_criteria.append(
            f"Citizenship rules explicitly include {citizenship_code}."
        )
    else:
        matched_criteria.append("The published record does not expose a restrictive citizenship filter.")

    normalized_gpa = normalize_gpa(profile.gpa_value, profile.gpa_scale)
    min_gpa = float(scholarship.min_gpa_value) if scholarship.min_gpa_value is not None else None
    gpa_alignment = _gpa_alignment_score(normalized_gpa, min_gpa)
    if min_gpa is None:
        rule_results.append(
            EligibilityRuleResult(
                key="gpa",
                label="GPA threshold",
                status="unknown",
                hard=False,
                student_value=str(normalized_gpa) if normalized_gpa is not None else None,
                scholarship_value=None,
                score=gpa_alignment,
                reason="Published scholarship does not list a GPA minimum.",
            )
        )
        constraint_notes.append(
            "The published record does not list a GPA minimum, which lowers ranking confidence."
        )
    elif normalized_gpa is None:
        rule_results.append(
            EligibilityRuleResult(
                key="gpa",
                label="GPA threshold",
                status="unknown",
                hard=False,
                student_value=None,
                scholarship_value=f"{min_gpa:.2f}/4.0",
                score=gpa_alignment,
                reason="Student GPA is missing, so GPA eligibility could not be fully confirmed.",
            )
        )
        constraint_notes.append(
            "Your GPA was not provided, so the GPA portion of fit could not be fully evaluated."
        )
    elif normalized_gpa < min_gpa:
        return None
    else:
        rule_results.append(
            EligibilityRuleResult(
                key="gpa",
                label="GPA threshold",
                status="pass",
                hard=True,
                student_value=f"{normalized_gpa:.2f}/4.0",
                scholarship_value=f"{min_gpa:.2f}/4.0",
                score=gpa_alignment,
                reason="Normalized GPA clears the published minimum.",
            )
        )
        matched_criteria.append(
            f"Your normalized GPA clears the published minimum of {min_gpa:.1f}."
        )

    field_alignment = field_alignment_score(profile.target_field, scholarship.field_tags)
    field_status = "pass" if field_alignment >= 0.7 else "unknown" if field_alignment >= 0.35 else "fail"
    field_reason = (
        "Field tags align strongly with the student's target field."
        if field_status == "pass"
        else "Field fit is adjacent rather than exact."
        if field_status == "unknown"
        else "Field tags do not align closely with the student's target field."
    )
    rule_results.append(
        EligibilityRuleResult(
            key="field_alignment",
            label="Field alignment",
            status=field_status,
            hard=False,
            student_value=profile.target_field,
            scholarship_value=", ".join(scholarship.field_tags[:5]) or None,
            score=field_alignment,
            reason=field_reason,
        )
    )
    if field_status == "pass":
        matched_criteria.append(
            f"Field fit is aligned with the published tags: {', '.join(scholarship.field_tags[:3])}."
        )
    else:
        constraint_notes.append(
            "Field fit is broader than exact, so review the program emphasis before shortlisting."
        )

    urgency = deadline_urgency_score(scholarship.deadline_at)
    rule_results.append(
        EligibilityRuleResult(
            key="deadline",
            label="Deadline urgency",
            status="pass" if urgency > 0 else "fail",
            hard=False,
            student_value=None,
            scholarship_value=scholarship.deadline_at.isoformat() if scholarship.deadline_at else None,
            score=urgency,
            reason="Open deadline supports current shortlist timing."
            if urgency > 0
            else "Published deadline has already passed.",
        )
    )
    if urgency == 0:
        return None

    passed_rule_count = sum(result.passed for result in rule_results)
    total_rule_count = len(rule_results)
    rule_pass_ratio = passed_rule_count / total_rule_count
    baseline_score = (
        (rule_pass_ratio * 0.4)
        + (field_alignment * 0.2)
        + (country_alignment * 0.2)
        + (gpa_alignment * 0.1)
        + (urgency * 0.1)
    )

    return MatchEvaluation(
        score=round(min(baseline_score, 0.99), 4),
        matched_criteria=matched_criteria,
        constraint_notes=constraint_notes,
        passed_rule_count=passed_rule_count,
        total_rule_count=total_rule_count,
        field_alignment=field_alignment,
        country_alignment=country_alignment,
        gpa_alignment=gpa_alignment,
        deadline_urgency=urgency,
        rule_results=rule_results,
        eligibility_graph=_build_eligibility_graph(profile, scholarship, rule_results),
    )


def _build_eligibility_graph(
    profile: StudentProfile,
    scholarship: Scholarship,
    rule_results: list[EligibilityRuleResult],
) -> dict[str, Any]:
    student_node_id = f"student:{profile.id}"
    scholarship_node_id = f"scholarship:{scholarship.id}"
    nodes: list[EligibilityGraphNode] = [
        EligibilityGraphNode(
            id=student_node_id,
            type="student",
            label="Student profile",
            metadata={
                "target_country_code": profile.target_country_code.upper(),
                "target_degree_level": profile.target_degree_level.value.upper(),
                "target_field": profile.target_field,
                "citizenship_country_code": profile.citizenship_country_code.upper(),
                "normalized_gpa": normalize_gpa(profile.gpa_value, profile.gpa_scale),
            },
        ),
        EligibilityGraphNode(
            id=scholarship_node_id,
            type="scholarship",
            label=scholarship.title,
            metadata={
                "country_code": scholarship.country_code.upper(),
                "degree_levels": scholarship.degree_levels,
                "field_tags": scholarship.field_tags,
                "citizenship_rules": scholarship.citizenship_rules,
                "min_gpa_value": float(scholarship.min_gpa_value) if scholarship.min_gpa_value is not None else None,
                "deadline_at": scholarship.deadline_at.isoformat() if scholarship.deadline_at else None,
            },
        ),
    ]
    edges: list[EligibilityGraphEdge] = []

    for rule in rule_results:
        rule_node_id = f"rule:{rule.key}"
        nodes.append(
            EligibilityGraphNode(
                id=rule_node_id,
                type="rule",
                label=rule.label,
                metadata=rule.as_dict(),
            )
        )
        edges.append(
            EligibilityGraphEdge(
                source=student_node_id,
                target=rule_node_id,
                relation="declares",
                status=rule.status,
                reason=rule.reason,
            )
        )
        edges.append(
            EligibilityGraphEdge(
                source=rule_node_id,
                target=scholarship_node_id,
                relation="evaluates",
                status=rule.status,
                reason=rule.reason,
            )
        )

    return {
        "nodes": [node.as_dict() for node in nodes],
        "edges": [edge.as_dict() for edge in edges],
        "summary": {
            "passed_rules": sum(rule.passed for rule in rule_results),
            "total_rules": len(rule_results),
            "hard_rules": sum(1 for rule in rule_results if rule.hard),
            "failed_rules": sum(1 for rule in rule_results if rule.status == "fail"),
        },
        "rules": [rule.as_dict() for rule in rule_results],
    }


def _gpa_alignment_score(
    normalized_gpa: float | None,
    min_gpa: float | None,
) -> float:
    if min_gpa is None:
        return 0.6
    if normalized_gpa is None:
        return 0.45
    if normalized_gpa < min_gpa:
        return 0.0

    margin = min(normalized_gpa - min_gpa, 1.0)
    return round(min(0.75 + (margin * 0.25), 1.0), 4)


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def _tokenize(value: str) -> set[str]:
    return {token for token in value.replace("/", " ").replace("-", " ").split() if token}
