import uuid
from datetime import datetime

from sqlalchemy import (
    String, Boolean, Integer, Text, Enum, DECIMAL,
    Date, TIMESTAMP, ForeignKey, Index, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(Enum("student", "mentor", "admin", "university", name="user_role"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    mentor_profile = relationship("Mentor", back_populates="user", uselist=False)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    gpa: Mapped[float] = mapped_column(DECIMAL(4, 2), nullable=True)
    gpa_scale: Mapped[float] = mapped_column(DECIMAL(4, 1), default=4.0)
    field_of_study: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_level: Mapped[str] = mapped_column(Enum("bachelor", "master", "phd", name="degree_level"), nullable=False)
    university: Mapped[str] = mapped_column(String(255), nullable=True)
    country_of_origin: Mapped[str] = mapped_column(String(100), nullable=True)
    target_countries = mapped_column(ARRAY(Text), nullable=True)
    research_publications: Mapped[int] = mapped_column(Integer, default=0)
    research_experience_months: Mapped[int] = mapped_column(Integer, default=0)
    leadership_roles: Mapped[int] = mapped_column(Integer, default=0)
    volunteer_hours: Mapped[int] = mapped_column(Integer, default=0)
    language_test_type: Mapped[str] = mapped_column(String(50), nullable=True)
    language_test_score: Mapped[float] = mapped_column(DECIMAL(4, 1), nullable=True)
    extracurricular_summary: Mapped[str] = mapped_column(Text, nullable=True)
    sop_draft: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="student_profile")
    applications = relationship("Application", back_populates="student")
    match_scores = relationship("MatchScore", back_populates="student")
    interview_sessions = relationship("InterviewSession", back_populates="student")


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    university: Mapped[str] = mapped_column(String(255), nullable=True)
    field_of_study = mapped_column(ARRAY(Text), nullable=True)
    degree_levels = mapped_column(ARRAY(Text), nullable=True)
    min_gpa: Mapped[float] = mapped_column(DECIMAL(4, 2), nullable=True)
    funding_type: Mapped[str] = mapped_column(Enum("full", "partial", "tuition", "stipend", name="funding_type"), nullable=True)
    funding_amount_usd: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=True)
    deadline = mapped_column(Date, nullable=True)
    required_documents = mapped_column(ARRAY(Text), nullable=True)
    eligibility_criteria = mapped_column(JSONB, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    simplified_description: Mapped[str] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scraped_at = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_scholarships_country", "country"),
        Index("idx_scholarships_deadline", "deadline", postgresql_where="is_active = TRUE"),
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    scholarship_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scholarships.id"))
    status: Mapped[str] = mapped_column(
        Enum("draft", "submitted", "under_review", "accepted", "rejected", name="application_status"),
        default="draft",
    )
    match_score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    success_probability: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    sop_version: Mapped[str] = mapped_column(Text, nullable=True)
    submitted_at = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="applications")

    __table_args__ = (
        Index("idx_applications_student", "student_id"),
    )


class MatchScore(Base):
    __tablename__ = "match_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    scholarship_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scholarships.id"))
    overall_score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    success_probability: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    feature_contributions = mapped_column(JSONB, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="match_scores")

    __table_args__ = (
        Index("idx_match_scores_student", "student_id"),
        Index("idx_match_scores_score", overall_score.desc()),
    )


class Mentor(Base):
    __tablename__ = "mentors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    scholarships_won = mapped_column(ARRAY(Text), nullable=True)
    fields_of_expertise = mapped_column(ARRAY(Text), nullable=True)
    university: Mapped[str] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    reputation_points: Mapped[int] = mapped_column(Integer, default=0)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    max_mentees: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="mentor_profile")
    sessions = relationship("MentorshipSession", back_populates="mentor")


class MentorshipSession(Base):
    __tablename__ = "mentorship_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mentor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mentors.id"))
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    session_type: Mapped[str] = mapped_column(
        Enum("sop_review", "mock_interview", "general_advice", name="session_type"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Enum("requested", "scheduled", "completed", "cancelled", name="session_status"), nullable=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    scheduled_at = mapped_column(TIMESTAMP, nullable=True)
    completed_at = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    mentor = relationship("Mentor", back_populates="sessions")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    document_type: Mapped[str] = mapped_column(
        Enum("transcript", "degree", "certificate", "recommendation", "language_test", name="document_type"),
        nullable=True,
    )
    document_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=True)
    institution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="credentials")

    __table_args__ = (
        Index("idx_credentials_hash", "document_hash"),
        Index("idx_credentials_student", "student_id"),
    )


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    scholarship_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scholarships.id"), nullable=True)
    audio_url: Mapped[str] = mapped_column(Text, nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    confidence_score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    clarity_score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    overall_score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    feedback = mapped_column(JSONB, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="interview_sessions")


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Enum("running", "success", "failed", name="scraper_status"), nullable=True)
    scholarships_found: Mapped[int] = mapped_column(Integer, default=0)
    scholarships_new: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    started_at = mapped_column(TIMESTAMP, nullable=True)
    completed_at = mapped_column(TIMESTAMP, nullable=True)
