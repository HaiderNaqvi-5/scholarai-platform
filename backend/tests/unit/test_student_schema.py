import pytest
from pydantic import ValidationError

from app.schemas.students import StudentProfileUpsertRequest


def test_profile_schema_rejects_gpa_above_scale() -> None:
    with pytest.raises(ValidationError):
        StudentProfileUpsertRequest(
            citizenship_country_code="pk",
            gpa_value=4.7,
            gpa_scale=4.0,
            target_field="Data Science",
            target_degree_level="MS",
            target_country_code="ca",
            language_test_type="IELTS",
            language_test_score=7.5,
        )
