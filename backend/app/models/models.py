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

from app.core.database import Base


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
        Enum(UserRole, name="user_role"),
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
        Enum(DegreeLevel, name="degree_level"),
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
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_document_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    degree_levels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    citizenship_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    min_gpa_value: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_state: Mapped[RecordState] = mapped_column(
        Enum(RecordState, name="scholarship_record_state"),
        nullable=False,
        default=RecordState.RAW,
    )
    provenance_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    __table_args__ = (
        Index("ix_scholarships_record_state", "record_state"),
        Index("ix_scholarships_country_code", "country_code"),
        Index("ix_scholarships_deadline_at", "deadline_at"),
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
        Enum(RequirementType, name="requirement_type"),
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
        Enum(ApplicationStatus, name="application_status"),
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
        Enum(DocumentType, name="document_type"),
        nullable=False,
    )
    input_method: Mapped[DocumentInputMethod] = mapped_column(
        Enum(DocumentInputMethod, name="document_input_method"),
        nullable=False,
    )
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    processing_status: Mapped[DocumentProcessingStatus] = mapped_column(
        Enum(DocumentProcessingStatus, name="document_processing_status"),
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
        Enum(DocumentProcessingStatus, name="document_feedback_status"),
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
