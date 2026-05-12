from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import DegreeLevel


_ALLOWED_DEGREES = {member.value for member in DegreeLevel}  # MS, PHD, MBA, MENG
_ALLOWED_HEC_DEGREES = {"bachelor", "master", "mphil"}
_ALLOWED_CGPA_SCALES = {"4.0", "4.0_hec"}
_ALLOWED_FUNDING_REQUIREMENTS = {"fully_funded_only", "partial_ok", "self_funded_ok"}
_ALLOWED_INTAKES = {"jan_2025", "sep_2025", "jan_2026", "sep_2026", "flexible"}


class StudentProfileUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citizenship_country_code: str = Field(min_length=2, max_length=2)
    gpa_value: float | None = Field(default=None, ge=0)
    gpa_scale: float = Field(default=4.0, gt=0)
    target_field: str = Field(min_length=2, max_length=120)
    target_degree_level: str = Field(default="MS")

    # legacy single-country (kept writable for back-compat; derived from target_countries when absent)
    target_country_code: str | None = Field(default=None, min_length=2, max_length=2)

    # Pakistan pivot — multi-country + multi-field
    target_countries: list[str] = Field(default_factory=list)
    target_fields: list[str] = Field(default_factory=list)

    language_test_type: str | None = Field(default=None, max_length=32)
    language_test_score: float | None = Field(default=None, ge=0)

    # Pakistani academic context
    hec_degree_level: str | None = Field(default=None, max_length=32)
    pakistani_university: str | None = Field(default=None, max_length=120)
    cgpa_scale_choice: str | None = Field(default=None, max_length=16)
    degree_subject: str | None = Field(default=None, max_length=120)
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)

    # test scores & research
    ielts_score: float | None = Field(default=None, ge=0, le=9)
    toefl_score: int | None = Field(default=None, ge=0, le=120)
    gre_quant: int | None = Field(default=None, ge=130, le=170)
    gre_verbal: int | None = Field(default=None, ge=130, le=170)
    has_research_publications: bool | None = None
    research_publication_count: int | None = Field(default=None, ge=0)

    # goals
    funding_requirement: str | None = Field(default=None, max_length=32)
    intake_target: str | None = Field(default=None, max_length=32)
    city_of_origin: str | None = Field(default=None, max_length=120)

    # financial context
    can_afford_application_fees: bool | None = None
    needs_gre_waiver: bool | None = None
    family_has_funds_for_bank_statement: bool | None = None

    @field_validator("citizenship_country_code")
    @classmethod
    def uppercase_citizenship(cls, value: str) -> str:
        return value.upper()

    @field_validator("target_country_code")
    @classmethod
    def uppercase_target_country(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("target_countries")
    @classmethod
    def normalize_target_countries(cls, value: list[str]) -> list[str]:
        return [c.upper() for c in value if isinstance(c, str) and len(c) == 2]

    @field_validator("target_fields")
    @classmethod
    def normalize_target_fields(cls, value: list[str]) -> list[str]:
        return [f.strip() for f in value if isinstance(f, str) and f.strip()]

    @field_validator("target_degree_level")
    @classmethod
    def enforce_supported_degree_level(cls, value: str) -> str:
        value = value.upper()
        if value not in _ALLOWED_DEGREES:
            raise ValueError(
                "target_degree_level must be one of: " + ", ".join(sorted(_ALLOWED_DEGREES))
            )
        return value

    @field_validator("hec_degree_level")
    @classmethod
    def validate_hec_degree_level(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in _ALLOWED_HEC_DEGREES:
            raise ValueError(
                "hec_degree_level must be one of: " + ", ".join(sorted(_ALLOWED_HEC_DEGREES))
            )
        return value

    @field_validator("cgpa_scale_choice")
    @classmethod
    def validate_cgpa_scale_choice(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in _ALLOWED_CGPA_SCALES:
            raise ValueError(
                "cgpa_scale_choice must be one of: " + ", ".join(sorted(_ALLOWED_CGPA_SCALES))
            )
        return value

    @field_validator("funding_requirement")
    @classmethod
    def validate_funding_requirement(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in _ALLOWED_FUNDING_REQUIREMENTS:
            raise ValueError(
                "funding_requirement must be one of: "
                + ", ".join(sorted(_ALLOWED_FUNDING_REQUIREMENTS))
            )
        return value

    @field_validator("intake_target")
    @classmethod
    def validate_intake_target(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in _ALLOWED_INTAKES:
            raise ValueError(
                "intake_target must be one of: " + ", ".join(sorted(_ALLOWED_INTAKES))
            )
        return value

    @model_validator(mode="after")
    def reconcile_countries_and_gpa(self) -> "StudentProfileUpsertRequest":
        if not self.target_countries and self.target_country_code:
            self.target_countries = [self.target_country_code]
        if not self.target_country_code and self.target_countries:
            self.target_country_code = self.target_countries[0]
        if not self.target_countries:
            raise ValueError("target_countries must include at least one ISO-2 country code")

        if not self.target_fields and self.target_field:
            self.target_fields = [self.target_field]

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
    target_countries: list[str]
    target_fields: list[str]
    language_test_type: str | None
    language_test_score: float | None

    hec_degree_level: str | None
    pakistani_university: str | None
    cgpa_scale_choice: str | None
    degree_subject: str | None
    graduation_year: int | None

    ielts_score: float | None
    toefl_score: int | None
    gre_quant: int | None
    gre_verbal: int | None
    has_research_publications: bool | None
    research_publication_count: int | None

    funding_requirement: str | None
    intake_target: str | None
    city_of_origin: str | None

    can_afford_application_fees: bool | None
    needs_gre_waiver: bool | None
    family_has_funds_for_bank_statement: bool | None
