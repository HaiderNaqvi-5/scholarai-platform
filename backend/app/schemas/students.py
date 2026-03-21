from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import DegreeLevel


class StudentProfileUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citizenship_country_code: str = Field(min_length=2, max_length=2)
    gpa_value: float | None = Field(default=None, ge=0)
    gpa_scale: float = Field(default=4.0, gt=0)
    target_field: str = Field(min_length=2, max_length=120)
    target_degree_level: str = Field(default="MS")
    target_country_code: str = Field(min_length=2, max_length=2)
    language_test_type: str | None = Field(default=None, max_length=32)
    language_test_score: float | None = Field(default=None, ge=0)

    @field_validator("citizenship_country_code", "target_country_code")
    @classmethod
    def uppercase_country_code(cls, value: str) -> str:
        return value.upper()

    @field_validator("target_degree_level")
    @classmethod
    def enforce_mvp_degree_level(cls, value: str) -> str:
        allowed_levels = {member.value for member in DegreeLevel}
        if value not in allowed_levels:
            allowed_text = ", ".join(sorted(allowed_levels))
            raise ValueError(
                f"ScholarAI MVP currently supports only these degree targets: {allowed_text}"
            )
        return value

    @model_validator(mode="after")
    def validate_gpa(self) -> "StudentProfileUpsertRequest":
        if self.gpa_value is not None and self.gpa_value > self.gpa_scale:
            raise ValueError("gpa_value cannot exceed gpa_scale")
        return self


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    citizenship_country_code: str
    gpa_value: float | None
    gpa_scale: float
    target_field: str
    target_degree_level: str
    target_country_code: str
    language_test_type: str | None
    language_test_score: float | None
