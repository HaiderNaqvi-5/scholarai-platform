import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base


def enum_values(enum_cls: type[enum.StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


class UserRole(enum.StrEnum):
    STUDENT = "student"
    ADMIN = "admin"


class DegreeLevel(enum.StrEnum):
    MS = "MS"


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

    scholarships: Mapped[list["Scholarship"]] = relationship(
        "Scholarship",
        back_populates="source_registry",
    )
    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        "IngestionRun",
        back_populates="source_registry",
        cascade="all, delete-orphan",
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
    external_source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    funding_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    funding_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    funding_amount_min: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    funding_amount_max: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_document_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    degree_levels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    citizenship_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    min_gpa_value: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_state: Mapped[RecordState] = mapped_column(
        Enum(RecordState, name="scholarship_record_state", values_callable=enum_values),
        nullable=False,
        default=RecordState.RAW,
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
    current_question_index: Mapped[int] = mapped_column(nullable=False, default=0)
    total_questions: Mapped[int] = mapped_column(nullable=False, default=0)
    question_set: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
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
