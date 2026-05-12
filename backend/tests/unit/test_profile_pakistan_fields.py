import pytest
from pydantic import ValidationError

from app.schemas.students import StudentProfileUpsertRequest


def _base_payload(**overrides):
    payload = dict(
        citizenship_country_code="pk",
        gpa_value=3.6,
        gpa_scale=4.0,
        target_field="Computer Science",
        target_degree_level="MS",
        target_countries=["uk", "de"],
    )
    payload.update(overrides)
    return payload


def test_target_countries_normalised_to_upper_and_derive_legacy_code() -> None:
    schema = StudentProfileUpsertRequest(**_base_payload())
    assert schema.target_countries == ["UK", "DE"]
    assert schema.target_country_code == "UK"


def test_legacy_target_country_code_populates_target_countries() -> None:
    payload = _base_payload()
    payload.pop("target_countries")
    payload["target_country_code"] = "ca"
    schema = StudentProfileUpsertRequest(**payload)
    assert schema.target_countries == ["CA"]


def test_missing_country_data_rejected() -> None:
    payload = _base_payload()
    payload.pop("target_countries")
    with pytest.raises(ValidationError):
        StudentProfileUpsertRequest(**payload)


def test_supports_phd_mba_meng_degree_targets() -> None:
    for level in ("PHD", "MBA", "MENG"):
        schema = StudentProfileUpsertRequest(**_base_payload(target_degree_level=level))
        assert schema.target_degree_level == level


def test_rejects_unknown_degree_level() -> None:
    with pytest.raises(ValidationError):
        StudentProfileUpsertRequest(**_base_payload(target_degree_level="DPHIL"))


def test_pakistan_fields_optional_but_validated() -> None:
    schema = StudentProfileUpsertRequest(
        **_base_payload(
            hec_degree_level="master",
            pakistani_university="NUST",
            cgpa_scale_choice="4.0_hec",
            degree_subject="CS",
            graduation_year=2025,
            ielts_score=7.0,
            funding_requirement="fully_funded_only",
            intake_target="sep_2026",
            city_of_origin="Islamabad",
            can_afford_application_fees=False,
            needs_gre_waiver=True,
            family_has_funds_for_bank_statement=True,
        )
    )
    assert schema.pakistani_university == "NUST"
    assert schema.funding_requirement == "fully_funded_only"


def test_unknown_hec_level_rejected() -> None:
    with pytest.raises(ValidationError):
        StudentProfileUpsertRequest(**_base_payload(hec_degree_level="diploma"))


def test_unknown_funding_requirement_rejected() -> None:
    with pytest.raises(ValidationError):
        StudentProfileUpsertRequest(**_base_payload(funding_requirement="part_funded"))


def test_target_fields_normalised() -> None:
    schema = StudentProfileUpsertRequest(
        **_base_payload(target_fields=["  cs ", "ds_ai", "  ", ""])
    )
    assert schema.target_fields == ["cs", "ds_ai"]


def test_target_fields_default_from_target_field() -> None:
    schema = StudentProfileUpsertRequest(**_base_payload())
    assert schema.target_fields == ["Computer Science"]
