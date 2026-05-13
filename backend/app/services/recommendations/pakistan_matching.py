"""Pakistan-tuned matching helpers for the recommendation engine (PRD §4).

Pure functions over dataclass-like inputs. No DB access — call sites build
the inputs from the StudentProfile + University rows they already have.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.cgpa_converter import (
    cgpa_explanation_note,
    pakistani_to_uk_class,
    pakistani_to_us_gpa,
)


@dataclass
class StudentSnapshot:
    cgpa_value: float | None
    pakistani_university: str | None
    target_countries: list[str]
    funding_requirement: str | None  # fully_funded_only | partial_ok | self_funded_ok
    can_afford_application_fees: bool | None
    needs_gre_waiver: bool | None
    ielts_score: float | None
    has_gre: bool


@dataclass
class UniversitySnapshot:
    name: str
    country: str
    accepts_hec_degrees: bool
    has_pakistani_alumni_network: bool
    offers_gta_gra: bool
    avg_visa_approval_rate_pk: float | None
    requires_gre: bool
    min_ielts_overall: float | None
    min_cgpa: float | None
    application_fee_usd: int | None
    application_fee_waiver_available: bool


@dataclass
class MatchResult:
    included: bool
    reason_excluded: str | None
    score: int
    tier: str  # safety | target | reach | excluded
    pakistan_context: dict


def _equivalent_us_gpa(cgpa: float | None) -> float | None:
    return pakistani_to_us_gpa(cgpa)


def _passes_hard_filters(student: StudentSnapshot, uni: UniversitySnapshot) -> tuple[bool, str | None]:
    if not uni.accepts_hec_degrees:
        return False, "University does not accept HEC-recognized degrees."

    target_countries = {c.upper() for c in student.target_countries}
    if target_countries and uni.country.upper() not in target_countries:
        return False, "University is not in your target countries."

    if uni.min_cgpa is not None and student.cgpa_value is not None:
        us_equiv = _equivalent_us_gpa(student.cgpa_value) or student.cgpa_value
        if us_equiv < float(uni.min_cgpa):
            return False, (
                f"Your US-equivalent GPA ({us_equiv:g}) is below the university minimum "
                f"({float(uni.min_cgpa):g})."
            )

    if uni.requires_gre and not student.has_gre:
        return False, "This program requires the GRE."

    if student.needs_gre_waiver and uni.requires_gre:
        return False, "This program requires the GRE and does not offer a waiver."

    if uni.min_ielts_overall is not None and student.ielts_score is not None:
        if float(student.ielts_score) < float(uni.min_ielts_overall):
            return False, (
                f"IELTS {float(student.ielts_score):g} is below the university minimum "
                f"({float(uni.min_ielts_overall):g})."
            )

    return True, None


def _soft_score(student: StudentSnapshot, uni: UniversitySnapshot) -> int:
    score = 50  # baseline
    if uni.has_pakistani_alumni_network:
        score += 10
    if uni.offers_gta_gra and student.funding_requirement == "fully_funded_only":
        score += 8
    if uni.application_fee_waiver_available:
        score += 5
    if uni.avg_visa_approval_rate_pk is not None and float(uni.avg_visa_approval_rate_pk) >= 0.7:
        score += 7
    if (
        uni.application_fee_usd is not None
        and uni.application_fee_usd > 100
        and student.can_afford_application_fees is False
    ):
        score -= 5
    return score


def _classify_tier(student: StudentSnapshot, uni: UniversitySnapshot, score: int) -> str:
    us_equiv = _equivalent_us_gpa(student.cgpa_value)
    min_cgpa = float(uni.min_cgpa) if uni.min_cgpa is not None else None

    if us_equiv is None or min_cgpa is None:
        if score >= 80:
            return "safety"
        if score >= 60:
            return "target"
        return "reach"

    if score >= 80 and us_equiv >= min_cgpa + 0.3:
        return "safety"
    if score >= 60 and abs(us_equiv - min_cgpa) <= 0.1:
        return "target"
    return "reach"


def _build_pakistan_context(student: StudentSnapshot, uni: UniversitySnapshot) -> dict:
    cgpa_note = cgpa_explanation_note(student.cgpa_value, student.pakistani_university)
    visa_rate = (
        float(uni.avg_visa_approval_rate_pk) if uni.avg_visa_approval_rate_pk is not None else None
    )
    return {
        "hec_recognized": uni.accepts_hec_degrees,
        "cgpa_equivalent_us": _equivalent_us_gpa(student.cgpa_value),
        "uk_degree_class": pakistani_to_uk_class(student.cgpa_value),
        "cgpa_note": cgpa_note,
        "gta_available": uni.offers_gta_gra,
        "gta_note": (
            f"{uni.name} regularly offers GTA/GRA positions to Pakistani MS students."
            if uni.offers_gta_gra
            else None
        ),
        "visa_note": (
            f"Estimated Pakistani student visa approval rate at {uni.name}: "
            f"{int(visa_rate * 100)}%."
            if visa_rate is not None
            else None
        ),
        "fee_waiver_note": (
            "Application fee waiver available — no upfront cost to apply."
            if uni.application_fee_waiver_available
            else None
        ),
        "pakistani_alumni_network": uni.has_pakistani_alumni_network,
    }


def evaluate_match(student: StudentSnapshot, uni: UniversitySnapshot) -> MatchResult:
    ok, reason = _passes_hard_filters(student, uni)
    pakistan_context = _build_pakistan_context(student, uni)
    if not ok:
        return MatchResult(
            included=False,
            reason_excluded=reason,
            score=0,
            tier="excluded",
            pakistan_context=pakistan_context,
        )
    score = _soft_score(student, uni)
    tier = _classify_tier(student, uni, score)
    return MatchResult(
        included=True,
        reason_excluded=None,
        score=score,
        tier=tier,
        pakistan_context=pakistan_context,
    )
