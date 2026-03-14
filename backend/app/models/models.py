"""
ScholarAI — SQLAlchemy ORM Models
Phase 1: pgvector 384-dim, removed mentors/mentorship_sessions,
         added AuditLog, HtmlSnapshot, EligibilityRequirement, EmbeddingCache.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    String, Boolean, Integer, Text, Enum, DECIMAL,
    Date, TIMESTAMP, ForeignKey, Index, CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


# ─────────────────────────────────────────────
#  Users & Auth
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # mentor role removed from enum (deferred module)
    role: Mapped[str] = mapped_column(
        Enum("student", "admin", name="user_role"), nullable=False, default="student"
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    student_profile: Mapped["StudentProfile"] = relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="admin")


# ─────────────────────────────────────────────
#  Student Profile (with 384-dim embedding)
# ─────────────────────────────────────────────

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    gpa: Mapped[float] = mapped_column(DECIMAL(4, 2), nullable=True)
    gpa_scale: Mapped[float] = mapped_column(DECIMAL(4, 1), default=4.0)
    field_of_study: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_level: Mapped[str] = mapped_column(
        Enum("bachelor", "master", "phd", name="degree_level_enum"), nullable=False
    )
    university: Mapped[str] = mapped_column(String(255), nullable=True)
    country_of_origin: Mapped[str] = mapped_column(String(100), nullable=True)
    target_countries: Mapped[list] = mapped_column(ARRAY(Text), nullable=True)
    citizenship: Mapped[str] = mapped_column(String(100), nullable=True)  # for eligibility graph

    # Research & Activity scores
    research_publications: Mapped[int] = mapped_column(Integer, default=0)
    research_experience_months: Mapped[int] = mapped_column(Integer, default=0)
    leadership_roles: Mapped[int] = mapped_column(Integer, default=0)
    volunteer_hours: Mapped[int] = mapped_column(Integer, default=0)

    # Language test
    language_test_type: Mapped[str] = mapped_column(String(50), nullable=True)
    language_test_score: Mapped[float] = mapped_column(DECIMAL(4, 1), nullable=True)

    extracurricular_summary: Mapped[str] = mapped_column(Text, nullable=True)
    sop_draft: Mapped[str] = mapped_column(Text, nullable=True)

    # ── 384-dim profile embedding ──────────────
    profile_embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="student_profile")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="student")
    match_scores: Mapped[list["MatchScore"]] = relationship("MatchScore", back_populates="student")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="student"
    )
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="student")

    __table_args__ = (
        # HNSW index for cosine similarity on profile embeddings
        Index(
            "idx_student_profile_embedding_hnsw",
            "profile_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"profile_embedding": "vector_cosine_ops"},
        ),
    )


# ─────────────────────────────────────────────
#  Scholarships (with 384-dim embedding)
# ─────────────────────────────────────────────

class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    university: Mapped[str] = mapped_column(String(255), nullable=True)
    field_of_study: Mapped[list] = mapped_column(ARRAY(Text), nullable=True)
    degree_levels: Mapped[list] = mapped_column(ARRAY(Text), nullable=True)
    min_gpa: Mapped[float] = mapped_column(DECIMAL(4, 2), nullable=True)
    funding_type: Mapped[str] = mapped_column(
        Enum("full", "partial", "tuition", "stipend", name="funding_type_enum"), nullable=True
    )
    funding_amount_usd: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=True)
    deadline: Mapped[Date] = mapped_column(Date, nullable=True)
    required_documents: Mapped[list] = mapped_column(ARRAY(Text), nullable=True)
    eligibility_criteria: Mapped[dict] = mapped_column(JSONB, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    simplified_description: Mapped[str] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_name: Mapped[str] = mapped_column(
        Enum("daad", "fulbright", "scholarships_ca", "scholarship_com", "other", name="source_name_enum"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_scraped_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # ── 384-dim scholarship embedding ──────────
    scholarship_embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    eligibility_requirements: Mapped[list["EligibilityRequirement"]] = relationship(
        "EligibilityRequirement", back_populates="scholarship", cascade="all, delete-orphan"
    )
    html_snapshots: Mapped[list["HtmlSnapshot"]] = relationship("HtmlSnapshot", back_populates="scholarship")
    match_scores: Mapped[list["MatchScore"]] = relationship("MatchScore", back_populates="scholarship")

    __table_args__ = (
        Index("idx_scholarships_country", "country"),
        Index("idx_scholarships_deadline", "deadline", postgresql_where="is_active = TRUE"),
        Index("idx_scholarships_source_name", "source_name"),
        # HNSW index for cosine similarity on scholarship embeddings
        Index(
            "idx_scholarship_embedding_hnsw",
            "scholarship_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"scholarship_embedding": "vector_cosine_ops"},
        ),
    )


# ─────────────────────────────────────────────
#  Eligibility Requirements
# ─────────────────────────────────────────────

class EligibilityRequirement(Base):
    __tablename__ = "eligibility_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scholarship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=False
    )
    requirement_type: Mapped[str] = mapped_column(
        Enum("citizenship", "gpa", "language", "degree_level", "field_of_study", "age", "other",
             name="requirement_type_enum"),
        nullable=False,
    )
    operator: Mapped[str] = mapped_column(String(10), nullable=True)  # >=, ==, IN, NOT_IN
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    scholarship: Mapped["Scholarship"] = relationship("Scholarship", back_populates="eligibility_requirements")

    __table_args__ = (
        Index("idx_eligibility_scholarship", "scholarship_id"),
    )


# ─────────────────────────────────────────────
#  Applications
# ─────────────────────────────────────────────

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    scholarship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scholarships.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum("draft", "submitted", "under_review", "accepted", "rejected", name="application_status_enum"),
        default="draft", nullable=False,
    )
    ai_match_score: Mapped[float] = mapped_column(DECIMAL(5, 4), nullable=True)
    success_probability: Mapped[float] = mapped_column(DECIMAL(5, 4), nullable=True)
    shap_explanation: Mapped[dict] = mapped_column(JSONB, nullable=True)
    lime_explanation: Mapped[dict] = mapped_column(JSONB, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="applications")

    __table_args__ = (
        Index("idx_applications_student", "student_id"),
        Index("idx_applications_scholarship", "scholarship_id"),
        Index("idx_applications_status", "status"),
    )


# ─────────────────────────────────────────────
#  Match Scores (cached recommendations)
# ─────────────────────────────────────────────

class MatchScore(Base):
    __tablename__ = "match_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    scholarship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scholarships.id"), nullable=False
    )
    overall_score: Mapped[float] = mapped_column(DECIMAL(5, 4), nullable=False)
    success_probability: Mapped[float] = mapped_column(DECIMAL(5, 4), nullable=True)
    vector_similarity: Mapped[float] = mapped_column(DECIMAL(5, 4), nullable=True)
    feature_contributions: Mapped[dict] = mapped_column(JSONB, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="match_scores")
    scholarship: Mapped["Scholarship"] = relationship("Scholarship", back_populates="match_scores")

    __table_args__ = (
        Index("idx_match_scores_student", "student_id"),
        Index("idx_match_scores_score", "overall_score"),
    )


# ─────────────────────────────────────────────
#  Documents (uploaded files with embeddings)
# ─────────────────────────────────────────────

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True
    )
    document_type: Mapped[str] = mapped_column(
        Enum("transcript", "sop", "lor", "cv", "language_test", "other", name="doc_type_enum"),
        nullable=False,
    )
    storage_url: Mapped[str] = mapped_column(Text, nullable=True)
    document_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)

    # ── 384-dim document content embedding ─────
    content_embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="documents")

    __table_args__ = (
        Index("idx_documents_student", "student_id"),
        Index("idx_documents_hash", "document_hash"),
    )


# ─────────────────────────────────────────────
#  Interview Sessions
# ─────────────────────────────────────────────

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    scholarship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scholarships.id"), nullable=True
    )
    questions: Mapped[dict] = mapped_column(JSONB, nullable=True)      # list of {question, answer, transcript}
    feedback: Mapped[dict] = mapped_column(JSONB, nullable=True)       # {clarity, relevance, depth, comments}
    overall_score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    audio_urls: Mapped[list] = mapped_column(ARRAY(Text), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    input_mode: Mapped[str] = mapped_column(
        Enum("text", "voice", name="interview_input_mode_enum"), default="text"
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="interview_sessions")

    __table_args__ = (
        Index("idx_interview_sessions_student", "student_id"),
    )


# ─────────────────────────────────────────────
#  HTML Snapshots (scraper debug storage)
# ─────────────────────────────────────────────

class HtmlSnapshot(Base):
    __tablename__ = "html_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scholarship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scholarships.id"), nullable=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    html_content: Mapped[str] = mapped_column(Text, nullable=True)
    http_status: Mapped[int] = mapped_column(Integer, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    job_id: Mapped[str] = mapped_column(String(255), nullable=True)   # Celery task ID

    scholarship: Mapped["Scholarship"] = relationship("Scholarship", back_populates="html_snapshots")

    __table_args__ = (
        Index("idx_html_snapshots_url", "source_url"),
        Index("idx_html_snapshots_job", "job_id"),
    )


# ─────────────────────────────────────────────
#  Scraper Runs (operational tracking)
# ─────────────────────────────────────────────

class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("running", "success", "failed", name="scraper_status_enum"), default="running"
    )
    scholarships_found: Mapped[int] = mapped_column(Integer, default=0)
    scholarships_new: Mapped[int] = mapped_column(Integer, default=0)
    scholarships_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_scraper_runs_status", "status"),
        Index("idx_scraper_runs_source", "source_name"),
    )


# ─────────────────────────────────────────────
#  Embedding Cache (avoid re-embedding same text)
# ─────────────────────────────────────────────

class EmbeddingCache(Base):
    __tablename__ = "embedding_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # SHA-256 of input text
    text_preview: Mapped[str] = mapped_column(String(200), nullable=True)
    embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="all-MiniLM-L6-v2")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_embedding_cache_hash", "text_hash"),
    )


# ─────────────────────────────────────────────
#  Audit Logs (admin operations)
# ─────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True  # nullable = system-generated events
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)   # e.g. "update_scholarship"
    target_table: Mapped[str] = mapped_column(String(100), nullable=True)
    target_id: Mapped[str] = mapped_column(String(255), nullable=True)
    old_value: Mapped[dict] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    admin: Mapped["User"] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_logs_admin", "admin_id"),
        Index("idx_audit_logs_created", "created_at"),
        Index("idx_audit_logs_target", "target_table", "target_id"),
    )
