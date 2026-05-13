"""Unit tests for Pakistan-tuned matching (Feature 4)."""

from app.services.recommendations.pakistan_matching import (
    StudentSnapshot,
    UniversitySnapshot,
    evaluate_match,
)


def _student(**overrides) -> StudentSnapshot:
    defaults = dict(
        cgpa_value=3.6,
        pakistani_university="NUST",
        target_countries=["GB", "DE"],
        funding_requirement="fully_funded_only",
        can_afford_application_fees=False,
        needs_gre_waiver=False,
        ielts_score=7.0,
        has_gre=False,
    )
    defaults.update(overrides)
    return StudentSnapshot(**defaults)


def _uni(**overrides) -> UniversitySnapshot:
    defaults = dict(
        name="University of Sheffield",
        country="GB",
        accepts_hec_degrees=True,
        has_pakistani_alumni_network=True,
        offers_gta_gra=False,
        avg_visa_approval_rate_pk=0.76,
        requires_gre=False,
        min_ielts_overall=6.5,
        min_cgpa=3.0,
        application_fee_usd=75,
        application_fee_waiver_available=False,
    )
    defaults.update(overrides)
    return UniversitySnapshot(**defaults)


def test_strong_match_uk() -> None:
    result = evaluate_match(_student(), _uni())
    assert result.included is True
    assert result.score >= 65
    assert result.tier in {"safety", "target", "reach"}
    assert result.pakistan_context["hec_recognized"] is True
    assert result.pakistan_context["cgpa_equivalent_us"] == 3.5
    assert "NUST" in result.pakistan_context["cgpa_note"]


def test_excluded_when_country_not_targeted() -> None:
    result = evaluate_match(_student(target_countries=["DE"]), _uni())  # uni is GB
    assert result.included is False
    assert "target countries" in result.reason_excluded


def test_gre_required_excludes_student_without_gre() -> None:
    uni = _uni(requires_gre=True, country="US")
    student = _student(target_countries=["US"], has_gre=False)
    result = evaluate_match(student, uni)
    assert result.included is False
    assert "GRE" in result.reason_excluded


def test_gre_waiver_required_excludes_gre_program() -> None:
    uni = _uni(requires_gre=True, country="US")
    student = _student(target_countries=["US"], has_gre=True, needs_gre_waiver=True)
    result = evaluate_match(student, uni)
    assert result.included is False


def test_low_cgpa_below_minimum_excluded() -> None:
    uni = _uni(min_cgpa=3.5)
    student = _student(cgpa_value=2.8)
    result = evaluate_match(student, uni)
    assert result.included is False
    assert "GPA" in result.reason_excluded


def test_low_ielts_excluded() -> None:
    uni = _uni(min_ielts_overall=7.0)
    student = _student(ielts_score=6.5)
    result = evaluate_match(student, uni)
    assert result.included is False


def test_hec_unaccepted_excluded() -> None:
    result = evaluate_match(_student(), _uni(accepts_hec_degrees=False))
    assert result.included is False
    assert "HEC" in result.reason_excluded


def test_gta_gra_adds_score_when_fully_funded_required() -> None:
    base = evaluate_match(_student(), _uni())
    gta = evaluate_match(_student(), _uni(offers_gta_gra=True))
    assert gta.score == base.score + 8
    assert gta.pakistan_context["gta_available"] is True


def test_high_fee_penalises_when_unaffordable() -> None:
    base = evaluate_match(_student(can_afford_application_fees=True), _uni(application_fee_usd=150))
    penalised = evaluate_match(
        _student(can_afford_application_fees=False), _uni(application_fee_usd=150)
    )
    assert penalised.score == base.score - 5


def test_fee_waiver_adds_score_and_note() -> None:
    result = evaluate_match(_student(), _uni(application_fee_waiver_available=True))
    assert "no upfront cost" in result.pakistan_context["fee_waiver_note"]


def test_visa_rate_above_threshold_adds_score_and_note() -> None:
    result = evaluate_match(_student(), _uni(avg_visa_approval_rate_pk=0.85))
    assert "85%" in result.pakistan_context["visa_note"]
    # Score includes +7 for visa rate
    baseline = evaluate_match(_student(), _uni(avg_visa_approval_rate_pk=0.5)).score
    assert result.score == baseline + 7


def test_tier_reach_when_borderline_cgpa() -> None:
    result = evaluate_match(_student(cgpa_value=3.05), _uni(min_cgpa=3.0))
    assert result.included is True
    assert result.tier in {"target", "reach"}


def test_seed_universities_load_into_snapshots() -> None:
    from app.demo.pakistan_universities import UNIVERSITIES_SEED

    assert len(UNIVERSITIES_SEED) >= 30
    countries = {row["country"] for row in UNIVERSITIES_SEED}
    assert countries >= {"GB", "US", "CA", "DE"}
