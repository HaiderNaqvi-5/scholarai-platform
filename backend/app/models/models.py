import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date as sa_Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base


def enum_values(enum_cls: type[enum.StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


class UserRole(enum.StrEnum):
    ENDUSER_STUDENT = "enduser_student"
    INTERNAL_USER = "internal_user"
    DEV = "dev"
    STUDENT = "student"
    ADMIN = "admin"
    MENTOR = "mentor"
    UNIVERSITY = "university"
    OWNER = "owner"


class CapabilityRiskTier(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InstitutionAccessLevel(enum.StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class DegreeLevel(enum.StrEnum):
    MS = "MS"
    PHD = "PHD"
    MBA = "MBA"
    MENG = "MENG"


class UserPlan(enum.StrEnum):
    FREE = "free"
    PRO = "pro"
    ELITE = "elite"
    INSTITUTION = "institution"


PLAN_RANK = {
    UserPlan.FREE: 0,
    UserPlan.PRO: 1,
    UserPlan.ELITE: 2,
    UserPlan.INSTITUTION: 3,
}


class InstitutionType(enum.StrEnum):
    SCHOOL = "school"
    UNIVERSITY = "university"
    HEC = "hec"
    OTHER = "other"


class ScholarshipTier(str, enum.Enum):
    STANDARD = "standard"
    PREMIUM = "premium"


class RecordState(enum.StrEnum):
    RAW = "raw"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class IngestionRunStatus(enum.StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class RequirementType(enum.StrEnum):
    CITIZENSHIP = "citizenship"
    GPA = "gpa"
    LANGUAGE = "language"
    DEGREE_LEVEL = "degree_level"
    FIELD = "field"
    COUNTRY = "country"
    OTHER = "other"


class ApplicationStatus(enum.StrEnum):
    SAVED = "saved"
    PLANNING = "planning"
    SUBMITTED = "submitted"
    CLOSED = "closed"


class DocumentType(enum.StrEnum):
    SOP = "sop"
    ESSAY = "essay"
    CV = "cv"
    PROFESSOR_EMAIL = "professor_email"  # Elite cold-email generator (PRD §0.6)
    STRATEGY_REPORT = "strategy_report"  # Elite application strategy report (PRD §0.6)
    INTERVIEW_TRANSCRIPT = "interview_transcript"  # Elite visa-interview transcript (PRD §0.6)


class DocumentInputMethod(enum.StrEnum):
    TEXT = "text"
    FILE = "file"


class DocumentProcessingStatus(enum.StrEnum):
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class InterviewSessionStatus(enum.StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class InterviewPracticeMode(enum.StrEnum):
    GENERAL = "general"
    SCHOLARSHIP = "scholarship"


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    seat_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dpa_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship("User", back_populates="institution")
    user_access_assignments: Mapped[list["UserInstitutionAccess"]] = relationship(
        "UserInstitutionAccess",
        back_populates="institution",
        cascade="all, delete-orphan",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=enum_values),
        default=UserRole.STUDENT,
        nullable=False,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auth_token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    plan: Mapped[str] = mapped_column(String(16), default="free", nullable=False)
    plan_currency: Mapped[str] = mapped_column(String(8), default="PKR", nullable=False)
    plan_activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    plan_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    billing_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    lifetime_sop_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Air University exhibition cohort capture (Q2-2026 trial launch).
    # Optional free-text so non-AU signups (later cohorts, other unis) work
    # without schema churn. Indexed on redeemed_invite_code for cohort filtering.
    air_uni_uni: Mapped[str | None] = mapped_column(String(64), nullable=True)
    air_uni_dept: Mapped[str | None] = mapped_column(String(32), nullable=True)
    air_uni_batch: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redeemed_invite_code: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )

    # Pakistan pivot — privacy / consent / soft-delete (Feature 9.5)
    data_consent_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    data_consent_granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_consent_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_consent_user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    b2b_share_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    b2b_share_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gdpr_erasure_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    account_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parent_consent_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_of_birth = mapped_column(sa_Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    student_profile: Mapped["StudentProfile | None"] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    applications: Mapped[list["Application"]] = relationship(
        "Application",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["DocumentRecord"]] = relationship(
        "DocumentRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(
        "InterviewSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    institution: Mapped["Institution | None"] = relationship("Institution", back_populates="users")
    capability_overrides: Mapped[list["UserCapability"]] = relationship(
        "UserCapability",
        foreign_keys="UserCapability.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    institution_access_assignments: Mapped[list["UserInstitutionAccess"]] = relationship(
        "UserInstitutionAccess",
        foreign_keys="UserInstitutionAccess.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Capability(Base):
    __tablename__ = "capabilities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    capability_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_tier: Mapped[CapabilityRiskTier] = mapped_column(
        Enum(CapabilityRiskTier, name="capability_risk_tier", values_callable=enum_values),
        nullable=False,
        default=CapabilityRiskTier.LOW,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    role_assignments: Mapped[list["RoleCapability"]] = relationship(
        "RoleCapability",
        back_populates="capability",
        cascade="all, delete-orphan",
    )
    user_assignments: Mapped[list["UserCapability"]] = relationship(
        "UserCapability",
        back_populates="capability",
        cascade="all, delete-orphan",
    )


class RoleCapability(Base):
    __tablename__ = "role_capabilities"

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=enum_values),
        primary_key=True,
    )
    capability_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("capabilities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    capability: Mapped["Capability"] = relationship("Capability", back_populates="role_assignments")


class UserCapability(Base):
    __tablename__ = "user_capabilities"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    capability_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("capabilities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    grant_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="capability_overrides",
    )
    capability: Mapped["Capability"] = relationship("Capability", back_populates="user_assignments")


class UserInstitutionAccess(Base):
    __tablename__ = "user_institution_access"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    access_level: Mapped[InstitutionAccessLevel] = mapped_column(
        Enum(InstitutionAccessLevel, name="institution_access_level", values_callable=enum_values),
        nullable=False,
        default=InstitutionAccessLevel.VIEWER,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="institution_access_assignments",
    )
    institution: Mapped["Institution"] = relationship(
        "Institution",
        back_populates="user_access_assignments",
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    citizenship_country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    gpa_value: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    gpa_scale: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False, default=4.0)
    target_field: Mapped[str] = mapped_column(String(120), nullable=False)
    target_degree_level: Mapped[DegreeLevel] = mapped_column(
        Enum(DegreeLevel, name="degree_level", values_callable=enum_values),
        nullable=False,
        default=DegreeLevel.MS,
    )
    target_country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    language_test_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language_test_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # --- Pakistan pivot fields (Feature 1) -------------------------------
    target_countries: Mapped[list[str]] = mapped_column(
        postgresql.ARRAY(String(2)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
        default=list,
    )
    target_fields: Mapped[list[str]] = mapped_column(
        postgresql.ARRAY(String(64)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
        default=list,
    )
    hec_degree_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pakistani_university: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cgpa_scale_choice: Mapped[str | None] = mapped_column(String(16), nullable=True)
    degree_subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    toefl_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ielts_score: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    gre_quant: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gre_verbal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_research_publications: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    research_publication_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    funding_requirement: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intake_target: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city_of_origin: Mapped[str | None] = mapped_column(String(120), nullable=True)
    can_afford_application_fees: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    needs_gre_waiver: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    family_has_funds_for_bank_statement: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # B2B-valuable contact + lead-scoring fields (Feature 9.5; nullable, opt-in)
    phone_e164: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp_e164: Mapped[str | None] = mapped_column(String(20), nullable=True)
    father_occupation: Mapped[str | None] = mapped_column(Text, nullable=True)
    household_income_band: Mapped[str | None] = mapped_column(String(16), nullable=True)
    current_employer: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_job_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    years_work_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    referral_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lead_score_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="student_profile")

    __table_args__ = (
        Index("ix_student_profiles_target_country", "target_country_code"),
        Index("ix_student_profiles_target_field", "target_field"),
    )


class SourceRegistry(Base):
    __tablename__ = "source_registry"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="official")
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(64), nullable=True)
    crawl_delay_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    discover_feeds: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        default=True,
    )
    # Source-health monitoring (migration 20260514_0021)
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_failure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        default=0,
    )
    health_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'unknown'"),
        default="unknown",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    scholarships: Mapped[list["Scholarship"]] = relationship(
        "Scholarship",
        back_populates="source_registry",
    )
    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        "IngestionRun",
        back_populates="source_registry",
        cascade="all, delete-orphan",
    )
    feeds: Mapped[list["SourceFeed"]] = relationship(
        "SourceFeed",
        back_populates="source",
        cascade="all, delete-orphan",
    )


class SourceFeed(Base):
    __tablename__ = "source_feed"
    __table_args__ = (
        Index("ix_source_feed_source_id", "source_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    feed_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    feed_type: Mapped[str] = mapped_column(String(16), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source: Mapped["SourceRegistry"] = relationship(
        "SourceRegistry",
        back_populates="feeds",
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    triggered_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[IngestionRunStatus] = mapped_column(
        Enum(IngestionRunStatus, name="ingestion_run_status", values_callable=enum_values),
        nullable=False,
        default=IngestionRunStatus.QUEUED,
    )
    fetch_url: Mapped[str] = mapped_column(Text, nullable=False)
    capture_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    parser_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    records_found: Mapped[int] = mapped_column(default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(default=0, nullable=False)
    records_skipped: Mapped[int] = mapped_column(default=0, nullable=False)
    run_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    source_registry: Mapped["SourceRegistry"] = relationship(
        "SourceRegistry",
        back_populates="ingestion_runs",
    )

    __table_args__ = (
        Index("ix_ingestion_runs_source_created_at", "source_registry_id", "created_at"),
        Index("ix_ingestion_runs_status", "status"),
    )


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_registry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_registry.id", ondelete="SET NULL"),
        nullable=True,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    funding_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    funding_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    funding_amount_min: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    funding_amount_max: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_document_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    degree_levels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    citizenship_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    min_gpa_value: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    record_state: Mapped[RecordState] = mapped_column(
        Enum(RecordState, name="scholarship_record_state", values_callable=enum_values),
        nullable=False,
        default=RecordState.RAW,
    )
    tier: Mapped[ScholarshipTier] = mapped_column(
        Enum(
            ScholarshipTier,
            name="scholarship_tier",
            values_callable=lambda x: [m.value for m in x],
        ),
        nullable=False,
        server_default=ScholarshipTier.STANDARD.value,
        default=ScholarshipTier.STANDARD,
        index=True,
    )
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unpublished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    source_registry: Mapped["SourceRegistry | None"] = relationship(
        "SourceRegistry",
        back_populates="scholarships",
    )
    requirements: Mapped[list["ScholarshipRequirement"]] = relationship(
        "ScholarshipRequirement",
        back_populates="scholarship",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[list["ScholarshipChunk"]] = relationship(
        "ScholarshipChunk",
        back_populates="scholarship",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_scholarships_record_state", "record_state"),
        Index("ix_scholarships_country_code", "country_code"),
        Index("ix_scholarships_deadline_at", "deadline_at"),
        Index("ix_scholarships_funding_type", "funding_type"),
        Index(
            "ix_scholarships_description_embedding_published",
            "description_embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"description_embedding": "vector_cosine_ops"},
            postgresql_where=text(
                "record_state = 'published'::scholarship_record_state "
                "AND description_embedding IS NOT NULL"
            ),
        ),
    )


class ScholarshipRequirement(Base):
    __tablename__ = "scholarship_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scholarship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scholarships.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_type: Mapped[RequirementType] = mapped_column(
        Enum(RequirementType, name="requirement_type", values_callable=enum_values),
        nullable=False,
    )
    operator: Mapped[str] = mapped_column(String(16), nullable=False, default="eq")
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    scholarship: Mapped["Scholarship"] = relationship(
        "Scholarship",
        back_populates="requirements",
    )

    __table_args__ = (Index("ix_scholarship_requirements_type", "requirement_type"),)


class ScholarshipChunk(Base):
    __tablename__ = "scholarship_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scholarship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scholarships.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=True) # 768 for sentence-transformers
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    scholarship: Mapped["Scholarship"] = relationship(
        "Scholarship",
        back_populates="chunks",
    )

    __table_args__ = (
        Index("ix_scholarship_chunks_embedding", "embedding", postgresql_using="ivfflat", postgresql_with={"lists": 100}, postgresql_ops={"embedding": "vector_cosine_ops"}),
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    scholarship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scholarships.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status", values_callable=enum_values),
        nullable=False,
        default=ApplicationStatus.SAVED,
    )
    estimated_fit_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    explanation_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="applications")
    scholarship: Mapped["Scholarship"] = relationship("Scholarship")

    __table_args__ = (
        Index("ix_applications_user_status", "user_id", "status"),
        Index("ix_applications_user_scholarship", "user_id", "scholarship_id", unique=True),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    before_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", values_callable=enum_values),
        nullable=False,
    )
    input_method: Mapped[DocumentInputMethod] = mapped_column(
        Enum(DocumentInputMethod, name="document_input_method", values_callable=enum_values),
        nullable=False,
    )
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    processing_status: Mapped[DocumentProcessingStatus] = mapped_column(
        Enum(
            DocumentProcessingStatus,
            name="document_processing_status",
            values_callable=enum_values,
        ),
        nullable=False,
        default=DocumentProcessingStatus.SUBMITTED,
    )
    scholarship_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scholarships.id", ondelete="SET NULL"),
        nullable=True,
    )
    latest_feedback_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="documents")
    feedback_entries: Mapped[list["DocumentFeedback"]] = relationship(
        "DocumentFeedback",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_documents_user_created_at", "user_id", "created_at"),
        Index("ix_documents_processing_status", "processing_status"),
    )


class DocumentFeedback(Base):
    __tablename__ = "document_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[DocumentProcessingStatus] = mapped_column(
        Enum(
            DocumentProcessingStatus,
            name="document_feedback_status",
            values_callable=enum_values,
        ),
        nullable=False,
        default=DocumentProcessingStatus.COMPLETED,
    )
    feedback_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    limitation_notice: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    document: Mapped["DocumentRecord"] = relationship(
        "DocumentRecord",
        back_populates="feedback_entries",
    )

    __table_args__ = (
        Index("ix_document_feedback_document_created_at", "document_id", "created_at"),
    )


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    practice_mode: Mapped[InterviewPracticeMode] = mapped_column(
        Enum(
            InterviewPracticeMode,
            name="interview_practice_mode",
            values_callable=enum_values,
        ),
        nullable=False,
        default=InterviewPracticeMode.GENERAL,
    )
    status: Mapped[InterviewSessionStatus] = mapped_column(
        Enum(
            InterviewSessionStatus,
            name="interview_session_status",
            values_callable=enum_values,
        ),
        nullable=False,
        default=InterviewSessionStatus.NOT_STARTED,
    )
    scholarship_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scholarships.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_question_index: Mapped[int] = mapped_column(nullable=False, default=0)
    total_questions: Mapped[int] = mapped_column(nullable=False, default=0)
    question_set: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    visa_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="interview_sessions")
    responses: Mapped[list["InterviewResponse"]] = relationship(
        "InterviewResponse",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_interview_sessions_user_created_at", "user_id", "created_at"),
        Index("ix_interview_sessions_status", "status"),
    )


class InterviewResponse(Base):
    __tablename__ = "interview_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_index: Mapped[int] = mapped_column(nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    summary_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession",
        back_populates="responses",
    )

    __table_args__ = (
        Index("ix_interview_responses_session_index", "session_id", "question_index", unique=True),
    )


class RecommendationKPISnapshot(Base):
    __tablename__ = "recommendation_kpi_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    kpi_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metrics_payload: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    gates_payload: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_recommendation_kpi_snapshots_user_created_at",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_recommendation_kpi_snapshots_policy_version",
            "policy_version",
        ),
    )


class DocumentKPISnapshot(Base):
    __tablename__ = "document_kpi_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    kpi_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metrics_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    gate_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_document_kpi_snapshots_user_created_at", "user_id", "created_at"),
        Index("ix_document_kpi_snapshots_document_id", "document_id"),
    )


class InterviewKPISnapshot(Base):
    __tablename__ = "interview_kpi_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    kpi_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metrics_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    gate_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_interview_kpi_snapshots_user_created_at", "user_id", "created_at"),
        Index("ix_interview_kpi_snapshots_session_id", "session_id"),
    )


# ============================================================================
# Pakistan pivot (Feature 1) — freemium / B2B scaffolding tables
# ============================================================================


class Waitlist(Base):
    __tablename__ = "waitlist"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(String(16), nullable=False, default="pro")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="PKR")
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class InstitutionStudent(Base):
    __tablename__ = "institution_students"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class University(Base):
    __tablename__ = "universities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepts_hec_degrees: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    has_pakistani_alumni_network: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    offers_gta_gra: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    avg_visa_approval_rate_pk: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    requires_gre: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    accepts_ielts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    accepts_toefl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_ielts_overall: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    min_ielts_each_band: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    min_cgpa: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    application_fee_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    application_fee_waiver_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    intake_months: Mapped[list[str]] = mapped_column(
        postgresql.ARRAY(String(12)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
        default=list,
    )
    fields_offered: Mapped[list[str]] = mapped_column(
        postgresql.ARRAY(String(64)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
        default=list,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_universities_country", "country"),
        Index("ix_universities_name", "name"),
    )


class VisaInterviewQuestion(Base):
    __tablename__ = "visa_interview_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    visa_type: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    ideal_answer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(8), nullable=False, default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_visa_q_country_visa_active", "country", "visa_type", "is_active"),
    )


class TrackerStage(enum.StrEnum):
    RESEARCHING = "researching"
    PREPARING = "preparing"
    APPLIED = "applied"
    INTERVIEW = "interview"
    DECISION = "decision"
    ACCEPTED = "accepted"


TRACKER_STAGES: tuple[str, ...] = tuple(member.value for member in TrackerStage)


_DEFAULT_DOCUMENT_CHECKLIST: dict[str, bool] = {
    "transcripts": False,
    "degree_certificate": False,
    "ielts_certificate": False,
    "gre_scores": False,
    "sop_draft": False,
    "sop_final": False,
    "cv_resume": False,
    "lor_1": False,
    "lor_2": False,
    "lor_3": False,
    "bank_statement": False,
    "hec_attestation": False,
    "passport_copy": False,
    "application_fee_paid": False,
}


def default_document_checklist() -> dict[str, bool]:
    return dict(_DEFAULT_DOCUMENT_CHECKLIST)


class ApplicationTrackerItem(Base):
    __tablename__ = "application_tracker_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scholarship_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scholarships.id", ondelete="SET NULL"),
        nullable=True,
    )
    university_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universities.id", ondelete="SET NULL"),
        nullable=True,
    )
    program_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    university_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default=TrackerStage.RESEARCHING.value)
    deadline = mapped_column(sa_Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_checklist: Mapped[dict] = mapped_column(
        postgresql.JSONB,
        nullable=False,
        default=default_document_checklist,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ConsentAuditLog(Base):
    __tablename__ = "consent_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consent_type: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[str] = mapped_column(String(16), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_consent_user_type_time", "user_id", "consent_type", "granted_at"),
    )


class DataExportRequest(Base):
    __tablename__ = "data_export_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    download_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)


class DataDeletionRequest(Base):
    __tablename__ = "data_deletion_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)


class UniversityLead(Base):
    __tablename__ = "university_leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    university_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universities.id", ondelete="SET NULL"),
        nullable=True,
    )
    share_reason: Mapped[str] = mapped_column(String(32), nullable=False)
    shared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    shared_with_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_snapshot: Mapped[dict] = mapped_column(
        postgresql.JSONB,
        nullable=False,
        default=dict,
    )
    consent_audit_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consent_audit_log.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_university_leads_university", "university_id"),
    )


class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    slug: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[str] = mapped_column(String(16), nullable=False)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_legal_doc_slug_current", "slug", "is_current"),
    )


class ReferralEnrollment(Base):
    __tablename__ = "referral_enrollments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    university_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fee_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    invoiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class SopMonthlyUsage(Base):
    """Per-user monthly SOP count for Pro/Elite quota gating. Free uses User.lifetime_sop_count."""

    __tablename__ = "sop_monthly_usage"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    period_yyyymm: Mapped[str] = mapped_column(String(6), primary_key=True)
    sop_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UsageLedger(Base):
    """Burn-cap accounting: LLM + WhatsApp cost per user per period, in PKR x 1e6 (BigInteger)."""

    __tablename__ = "usage_ledger"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_yyyymm: Mapped[str] = mapped_column(String(6), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    input_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    cost_pkr_micro: Mapped[int] = mapped_column(BigInteger, nullable=False)
    endpoint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class InviteCode(Base):
    """Shared invite code for cohort trial grants.

    A single code (e.g. ``AIRU2026``) is redeemable up to ``max_uses`` times
    inside the ``[valid_from, valid_until]`` window. Each redemption grants
    the consuming user ``grants_plan`` for ``trial_days`` days from the
    redemption moment (set by the auth service via ``user.plan_expires_at``).
    The ``cohort`` column lets us bulk-issue more than one code per audience
    later (e.g. ``NUST2026``, ``COMSATS2026``) without schema churn.
    """

    __tablename__ = "invite_codes"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    cohort: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    grants_plan: Mapped[str] = mapped_column(String(16), nullable=False)
    trial_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30, server_default="30"
    )
    max_uses: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default="100"
    )
    uses: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

