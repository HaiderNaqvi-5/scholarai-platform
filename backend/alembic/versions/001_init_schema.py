"""initial schema

Revision ID: 001_init_schema
Revises:
Create Date: 2026-03-14 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "001_init_schema"
down_revision = None
branch_labels = None
depends_on = None


user_role_enum = postgresql.ENUM("student", "admin", name="user_role")
degree_level_enum = postgresql.ENUM("bachelor", "master", "phd", name="degree_level_enum")
funding_type_enum = postgresql.ENUM("full", "partial", "tuition", "stipend", name="funding_type_enum")
source_name_enum = postgresql.ENUM(
    "daad",
    "fulbright",
    "scholarships_ca",
    "scholarship_com",
    "other",
    name="source_name_enum",
)
requirement_type_enum = postgresql.ENUM(
    "citizenship",
    "gpa",
    "language",
    "degree_level",
    "field_of_study",
    "age",
    "other",
    name="requirement_type_enum",
)
application_status_enum = postgresql.ENUM(
    "draft",
    "submitted",
    "under_review",
    "accepted",
    "rejected",
    name="application_status_enum",
)
doc_type_enum = postgresql.ENUM(
    "transcript",
    "sop",
    "lor",
    "cv",
    "language_test",
    "other",
    name="doc_type_enum",
)
interview_input_mode_enum = postgresql.ENUM("text", "voice", name="interview_input_mode_enum")
scraper_status_enum = postgresql.ENUM("running", "success", "failed", name="scraper_status_enum")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    bind = op.get_bind()
    for enum_type in (
        user_role_enum,
        degree_level_enum,
        funding_type_enum,
        source_name_enum,
        requirement_type_enum,
        application_status_enum,
        doc_type_enum,
        interview_input_mode_enum,
        scraper_status_enum,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "student_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gpa", sa.DECIMAL(4, 2), nullable=True),
        sa.Column("gpa_scale", sa.DECIMAL(4, 1), nullable=True, server_default=sa.text("4.0")),
        sa.Column("field_of_study", sa.String(length=255), nullable=False),
        sa.Column("degree_level", degree_level_enum, nullable=False),
        sa.Column("university", sa.String(length=255), nullable=True),
        sa.Column("country_of_origin", sa.String(length=100), nullable=True),
        sa.Column("target_countries", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("citizenship", sa.String(length=100), nullable=True),
        sa.Column("research_publications", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("research_experience_months", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("leadership_roles", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("volunteer_hours", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("language_test_type", sa.String(length=50), nullable=True),
        sa.Column("language_test_score", sa.DECIMAL(4, 1), nullable=True),
        sa.Column("extracurricular_summary", sa.Text(), nullable=True),
        sa.Column("sop_draft", sa.Text(), nullable=True),
        sa.Column("profile_embedding", Vector(dim=384), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "scholarships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("university", sa.String(length=255), nullable=True),
        sa.Column("field_of_study", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("degree_levels", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("min_gpa", sa.DECIMAL(4, 2), nullable=True),
        sa.Column("funding_type", funding_type_enum, nullable=True),
        sa.Column("funding_amount_usd", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("required_documents", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("eligibility_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("simplified_description", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_name", source_name_enum, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_scraped_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("scholarship_embedding", Vector(dim=384), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_url"),
    )

    op.create_table(
        "eligibility_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_type", requirement_type_enum, nullable=False),
        sa.Column("operator", sa.String(length=10), nullable=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["scholarship_id"], ["scholarships.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", application_status_enum, nullable=False, server_default=sa.text("'draft'")),
        sa.Column("ai_match_score", sa.DECIMAL(5, 4), nullable=True),
        sa.Column("success_probability", sa.DECIMAL(5, 4), nullable=True),
        sa.Column("shap_explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("lime_explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["scholarship_id"], ["scholarships.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "match_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.DECIMAL(5, 4), nullable=False),
        sa.Column("success_probability", sa.DECIMAL(5, 4), nullable=True),
        sa.Column("vector_similarity", sa.DECIMAL(5, 4), nullable=True),
        sa.Column("feature_contributions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["scholarship_id"], ["scholarships.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_type", doc_type_enum, nullable=False),
        sa.Column("storage_url", sa.Text(), nullable=True),
        sa.Column("document_hash", sa.String(length=64), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("content_embedding", Vector(dim=384), nullable=True),
        sa.Column("uploaded_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("questions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("feedback", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("overall_score", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("audio_urls", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("input_mode", interview_input_mode_enum, nullable=False, server_default=sa.text("'text'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["scholarship_id"], ["scholarships.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "html_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("html_content", sa.Text(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("scraped_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("job_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["scholarship_id"], ["scholarships.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scraper_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("status", scraper_status_enum, nullable=False, server_default=sa.text("'running'")),
        sa.Column("scholarships_found", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("scholarships_new", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("scholarships_updated", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "embedding_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("text_preview", sa.String(length=200), nullable=True),
        sa.Column("embedding", Vector(dim=384), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False, server_default=sa.text("'all-MiniLM-L6-v2'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("text_hash"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admin_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_table", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.String(length=255), nullable=True),
        sa.Column("old_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_student_profile_embedding_hnsw",
        "student_profiles",
        ["profile_embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"profile_embedding": "vector_cosine_ops"},
    )
    op.create_index("idx_scholarships_country", "scholarships", ["country"], unique=False)
    op.create_index(
        "idx_scholarships_deadline",
        "scholarships",
        ["deadline"],
        unique=False,
        postgresql_where=sa.text("is_active = TRUE"),
    )
    op.create_index("idx_scholarships_source_name", "scholarships", ["source_name"], unique=False)
    op.create_index(
        "idx_scholarship_embedding_hnsw",
        "scholarships",
        ["scholarship_embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"scholarship_embedding": "vector_cosine_ops"},
    )
    op.create_index("idx_eligibility_scholarship", "eligibility_requirements", ["scholarship_id"], unique=False)
    op.create_index("idx_applications_student", "applications", ["student_id"], unique=False)
    op.create_index("idx_applications_scholarship", "applications", ["scholarship_id"], unique=False)
    op.create_index("idx_applications_status", "applications", ["status"], unique=False)
    op.create_index("idx_match_scores_student", "match_scores", ["student_id"], unique=False)
    op.create_index("idx_match_scores_score", "match_scores", ["overall_score"], unique=False)
    op.create_index("idx_documents_student", "documents", ["student_id"], unique=False)
    op.create_index("idx_documents_hash", "documents", ["document_hash"], unique=False)
    op.create_index("idx_interview_sessions_student", "interview_sessions", ["student_id"], unique=False)
    op.create_index("idx_html_snapshots_url", "html_snapshots", ["source_url"], unique=False)
    op.create_index("idx_html_snapshots_job", "html_snapshots", ["job_id"], unique=False)
    op.create_index("idx_scraper_runs_status", "scraper_runs", ["status"], unique=False)
    op.create_index("idx_scraper_runs_source", "scraper_runs", ["source_name"], unique=False)
    op.create_index("idx_embedding_cache_hash", "embedding_cache", ["text_hash"], unique=False)
    op.create_index("idx_audit_logs_admin", "audit_logs", ["admin_id"], unique=False)
    op.create_index("idx_audit_logs_created", "audit_logs", ["created_at"], unique=False)
    op.create_index("idx_audit_logs_target", "audit_logs", ["target_table", "target_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_audit_logs_target", table_name="audit_logs")
    op.drop_index("idx_audit_logs_created", table_name="audit_logs")
    op.drop_index("idx_audit_logs_admin", table_name="audit_logs")
    op.drop_index("idx_embedding_cache_hash", table_name="embedding_cache")
    op.drop_index("idx_scraper_runs_source", table_name="scraper_runs")
    op.drop_index("idx_scraper_runs_status", table_name="scraper_runs")
    op.drop_index("idx_html_snapshots_job", table_name="html_snapshots")
    op.drop_index("idx_html_snapshots_url", table_name="html_snapshots")
    op.drop_index("idx_interview_sessions_student", table_name="interview_sessions")
    op.drop_index("idx_documents_hash", table_name="documents")
    op.drop_index("idx_documents_student", table_name="documents")
    op.drop_index("idx_match_scores_score", table_name="match_scores")
    op.drop_index("idx_match_scores_student", table_name="match_scores")
    op.drop_index("idx_applications_status", table_name="applications")
    op.drop_index("idx_applications_scholarship", table_name="applications")
    op.drop_index("idx_applications_student", table_name="applications")
    op.drop_index("idx_eligibility_scholarship", table_name="eligibility_requirements")
    op.drop_index("idx_scholarship_embedding_hnsw", table_name="scholarships", postgresql_using="hnsw")
    op.drop_index("idx_scholarships_source_name", table_name="scholarships")
    op.drop_index("idx_scholarships_deadline", table_name="scholarships")
    op.drop_index("idx_scholarships_country", table_name="scholarships")
    op.drop_index("idx_student_profile_embedding_hnsw", table_name="student_profiles", postgresql_using="hnsw")
    op.drop_index("ix_users_email", table_name="users")

    op.drop_table("audit_logs")
    op.drop_table("embedding_cache")
    op.drop_table("scraper_runs")
    op.drop_table("html_snapshots")
    op.drop_table("interview_sessions")
    op.drop_table("documents")
    op.drop_table("match_scores")
    op.drop_table("applications")
    op.drop_table("eligibility_requirements")
    op.drop_table("scholarships")
    op.drop_table("student_profiles")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_type in (
        scraper_status_enum,
        interview_input_mode_enum,
        doc_type_enum,
        application_status_enum,
        requirement_type_enum,
        source_name_enum,
        funding_type_enum,
        degree_level_enum,
        user_role_enum,
    ):
        enum_type.drop(bind, checkfirst=True)

    op.execute("DROP EXTENSION IF EXISTS vector")
