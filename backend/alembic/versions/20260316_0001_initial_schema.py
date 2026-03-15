"""Initial ScholarAI MVP schema

Revision ID: 20260316_0001
Revises: None
Create Date: 2026-03-16 02:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260316_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    user_role = postgresql.ENUM("student", "admin", name="user_role", create_type=False)
    degree_level = postgresql.ENUM("MS", name="degree_level", create_type=False)
    scholarship_record_state = postgresql.ENUM(
        "raw",
        "validated",
        "published",
        "archived",
        name="scholarship_record_state",
        create_type=False,
    )
    requirement_type = postgresql.ENUM(
        "citizenship",
        "gpa",
        "language",
        "degree_level",
        "field",
        "country",
        "other",
        name="requirement_type",
        create_type=False,
    )
    application_status = postgresql.ENUM(
        "saved",
        "planning",
        "submitted",
        "closed",
        name="application_status",
        create_type=False,
    )
    document_type = postgresql.ENUM("sop", "essay", name="document_type", create_type=False)
    document_input_method = postgresql.ENUM(
        "text", "file", name="document_input_method", create_type=False
    )
    document_processing_status = postgresql.ENUM(
        "submitted",
        "processing",
        "completed",
        "failed",
        name="document_processing_status",
        create_type=False,
    )
    document_feedback_status = postgresql.ENUM(
        "submitted",
        "processing",
        "completed",
        "failed",
        name="document_feedback_status",
        create_type=False,
    )
    interview_practice_mode = postgresql.ENUM(
        "general", name="interview_practice_mode", create_type=False
    )
    interview_session_status = postgresql.ENUM(
        "not_started",
        "in_progress",
        "completed",
        name="interview_session_status",
        create_type=False,
    )

    for enum_type in [
        user_role,
        degree_level,
        scholarship_record_state,
        requirement_type,
        application_status,
        document_type,
        document_input_method,
        document_processing_status,
        document_feedback_status,
        interview_practice_mode,
        interview_session_status,
    ]:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "source_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_key", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key"),
    )

    op.create_table(
        "student_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("citizenship_country_code", sa.String(length=2), nullable=False),
        sa.Column("gpa_value", sa.Numeric(4, 2), nullable=True),
        sa.Column("gpa_scale", sa.Numeric(4, 1), nullable=False),
        sa.Column("target_field", sa.String(length=120), nullable=False),
        sa.Column("target_degree_level", degree_level, nullable=False),
        sa.Column("target_country_code", sa.String(length=2), nullable=False),
        sa.Column("language_test_type", sa.String(length=32), nullable=True),
        sa.Column("language_test_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_student_profiles_target_country", "student_profiles", ["target_country_code"], unique=False)
    op.create_index("ix_student_profiles_target_field", "student_profiles", ["target_field"], unique=False)

    op.create_table(
        "scholarships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_registry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_source_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("provider_name", sa.String(length=255), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("funding_summary", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_document_ref", sa.String(length=255), nullable=True),
        sa.Column("field_tags", sa.JSON(), nullable=False),
        sa.Column("degree_levels", sa.JSON(), nullable=False),
        sa.Column("citizenship_rules", sa.JSON(), nullable=False),
        sa.Column("min_gpa_value", sa.Numeric(4, 2), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("record_state", scholarship_record_state, nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance_payload", sa.JSON(), nullable=True),
        sa.Column("source_last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unpublished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["published_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_registry_id"], ["source_registry.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["validated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_url"),
    )
    op.create_index("ix_scholarships_record_state", "scholarships", ["record_state"], unique=False)
    op.create_index("ix_scholarships_country_code", "scholarships", ["country_code"], unique=False)
    op.create_index("ix_scholarships_deadline_at", "scholarships", ["deadline_at"], unique=False)

    op.create_table(
        "scholarship_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_type", requirement_type, nullable=False),
        sa.Column("operator", sa.String(length=16), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scholarship_id"], ["scholarships.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scholarship_requirements_type", "scholarship_requirements", ["requirement_type"], unique=False)

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", application_status, nullable=False),
        sa.Column("estimated_fit_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("explanation_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scholarship_id"], ["scholarships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_applications_user_status", "applications", ["user_id", "status"], unique=False)
    op.create_index("ix_applications_user_scholarship", "applications", ["user_id", "scholarship_id"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_type", document_type, nullable=False),
        sa.Column("input_method", document_input_method, nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("storage_path", sa.String(length=512), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("processing_status", document_processing_status, nullable=False),
        sa.Column("latest_feedback_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_user_created_at", "documents", ["user_id", "created_at"], unique=False)
    op.create_index("ix_documents_processing_status", "documents", ["processing_status"], unique=False)

    op.create_table(
        "document_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", document_feedback_status, nullable=False),
        sa.Column("feedback_payload", sa.JSON(), nullable=False),
        sa.Column("limitation_notice", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_feedback_document_created_at",
        "document_feedback",
        ["document_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("practice_mode", interview_practice_mode, nullable=False),
        sa.Column("status", interview_session_status, nullable=False),
        sa.Column("current_question_index", sa.Integer(), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("question_set", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_sessions_user_created_at", "interview_sessions", ["user_id", "created_at"], unique=False)
    op.create_index("ix_interview_sessions_status", "interview_sessions", ["status"], unique=False)

    op.create_table(
        "interview_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_index", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("score_payload", sa.JSON(), nullable=False),
        sa.Column("summary_feedback", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_interview_responses_session_index",
        "interview_responses",
        ["session_id", "question_index"],
        unique=True,
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_interview_responses_session_index", table_name="interview_responses")
    op.drop_table("interview_responses")
    op.drop_index("ix_interview_sessions_status", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_user_created_at", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    op.drop_index("ix_document_feedback_document_created_at", table_name="document_feedback")
    op.drop_table("document_feedback")
    op.drop_index("ix_documents_processing_status", table_name="documents")
    op.drop_index("ix_documents_user_created_at", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_applications_user_scholarship", table_name="applications")
    op.drop_index("ix_applications_user_status", table_name="applications")
    op.drop_table("applications")
    op.drop_index("ix_scholarship_requirements_type", table_name="scholarship_requirements")
    op.drop_table("scholarship_requirements")
    op.drop_index("ix_scholarships_deadline_at", table_name="scholarships")
    op.drop_index("ix_scholarships_country_code", table_name="scholarships")
    op.drop_index("ix_scholarships_record_state", table_name="scholarships")
    op.drop_table("scholarships")
    op.drop_index("ix_student_profiles_target_field", table_name="student_profiles")
    op.drop_index("ix_student_profiles_target_country", table_name="student_profiles")
    op.drop_table("student_profiles")
    op.drop_table("source_registry")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    for enum_name in [
        "interview_session_status",
        "interview_practice_mode",
        "document_feedback_status",
        "document_processing_status",
        "document_input_method",
        "document_type",
        "application_status",
        "requirement_type",
        "scholarship_record_state",
        "degree_level",
        "user_role",
    ]:
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
