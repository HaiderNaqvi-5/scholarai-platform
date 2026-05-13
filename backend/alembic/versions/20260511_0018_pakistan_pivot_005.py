"""pakistan pivot 005: B2B student-data capture + consent / privacy hardening

Revision ID: 20260511_0018
Revises: 20260511_0017
Create Date: 2026-05-11 19:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260511_0018"
down_revision: Union[str, None] = "20260511_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # ---------------------------------------------------------------------
    # users: consent + soft-delete + marketing/B2B grant flags
    # ---------------------------------------------------------------------
    user_columns = [
        ("data_consent_version", sa.String(16)),
        ("data_consent_granted_at", sa.DateTime(timezone=True)),
        ("data_consent_ip", sa.String(64)),
        ("data_consent_user_agent", sa.Text()),
        ("marketing_consent", sa.Boolean(), False),
        ("b2b_share_consent", sa.Boolean(), False),
        ("b2b_share_consent_at", sa.DateTime(timezone=True)),
        ("gdpr_erasure_requested_at", sa.DateTime(timezone=True)),
        ("account_deleted_at", sa.DateTime(timezone=True)),
        ("parent_consent_email", sa.Text()),
        ("parent_consent_at", sa.DateTime(timezone=True)),
        ("date_of_birth", sa.Date()),
    ]
    for entry in user_columns:
        if len(entry) == 2:
            name, sa_type = entry
            default = None
        else:
            name, sa_type, default = entry
        if _has_column(inspector, "users", name):
            continue
        kwargs = {"nullable": True}
        if default is not None:
            kwargs["server_default"] = sa.text("false" if isinstance(default, bool) and default is False else "true")
            kwargs["nullable"] = False
        op.add_column("users", sa.Column(name, sa_type, **kwargs))

    # ---------------------------------------------------------------------
    # student_profiles: B2B-valuable fields
    # ---------------------------------------------------------------------
    profile_columns = [
        ("phone_e164", sa.String(20)),
        ("whatsapp_e164", sa.String(20)),
        ("father_occupation", sa.Text()),
        ("household_income_band", sa.String(16)),
        ("current_employer", sa.Text()),
        ("current_job_title", sa.Text()),
        ("years_work_experience", sa.Integer()),
        ("linkedin_url", sa.Text()),
        ("github_url", sa.Text()),
        ("referral_source", sa.String(32)),
        ("lead_score", sa.Integer(), 0),
        ("lead_score_updated_at", sa.DateTime(timezone=True)),
    ]
    for entry in profile_columns:
        if len(entry) == 2:
            name, sa_type = entry
            default = None
        else:
            name, sa_type, default = entry
        if _has_column(inspector, "student_profiles", name):
            continue
        kwargs = {"nullable": True}
        if default is not None:
            kwargs["server_default"] = sa.text(str(default))
            kwargs["nullable"] = False
        op.add_column("student_profiles", sa.Column(name, sa_type, **kwargs))

    # ---------------------------------------------------------------------
    # consent_audit_log (immutable record of every grant / revoke)
    # ---------------------------------------------------------------------
    if not _has_table(inspector, "consent_audit_log"):
        op.create_table(
            "consent_audit_log",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("consent_type", sa.String(32), nullable=False),
            sa.Column("version", sa.String(16), nullable=False),
            sa.Column("action", sa.String(16), nullable=False),
            sa.Column("ip", sa.String(64), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("document_sha256", sa.String(64), nullable=True),
            sa.Column(
                "granted_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint(
                "consent_type IN ('terms','privacy','marketing','b2b_share','cookies','aup')",
                name="ck_consent_type_allowed",
            ),
            sa.CheckConstraint(
                "action IN ('grant','revoke')",
                name="ck_consent_action_allowed",
            ),
        )
        op.create_index(
            "ix_consent_user_type_time",
            "consent_audit_log",
            ["user_id", "consent_type", "granted_at"],
        )

    # ---------------------------------------------------------------------
    # data_export_requests
    # ---------------------------------------------------------------------
    if not _has_table(inspector, "data_export_requests"):
        op.create_table(
            "data_export_requests",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "requested_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("download_url", sa.Text(), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
            sa.CheckConstraint(
                "status IN ('pending','running','completed','failed','expired')",
                name="ck_export_status_allowed",
            ),
        )

    # ---------------------------------------------------------------------
    # data_deletion_requests
    # ---------------------------------------------------------------------
    if not _has_table(inspector, "data_deletion_requests"):
        op.create_table(
            "data_deletion_requests",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "requested_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
            sa.CheckConstraint(
                "status IN ('pending','cancelled','executed','failed')",
                name="ck_deletion_status_allowed",
            ),
        )

    # ---------------------------------------------------------------------
    # university_leads (the B2B product surface)
    # ---------------------------------------------------------------------
    if not _has_table(inspector, "university_leads"):
        op.create_table(
            "university_leads",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "university_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("universities.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("share_reason", sa.String(32), nullable=False),
            sa.Column(
                "shared_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("shared_with_email", sa.Text(), nullable=True),
            sa.Column(
                "profile_snapshot",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "consent_audit_log_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("consent_audit_log.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.CheckConstraint(
                "share_reason IN ('match','explicit_application','paid_referral')",
                name="ck_university_lead_reason_allowed",
            ),
        )
        op.create_index(
            "ix_university_leads_university",
            "university_leads",
            ["university_id"],
        )

    # ---------------------------------------------------------------------
    # legal_documents (versioned terms / privacy / cookies / b2b_data_use / aup)
    # ---------------------------------------------------------------------
    if not _has_table(inspector, "legal_documents"):
        op.create_table(
            "legal_documents",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("slug", sa.String(32), nullable=False),
            sa.Column("version", sa.String(16), nullable=False),
            sa.Column("body_markdown", sa.Text(), nullable=False),
            sa.Column("sha256_hash", sa.String(64), nullable=False),
            sa.Column(
                "effective_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "is_current",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint(
                "slug IN ('terms','privacy','cookies','b2b_data_use','aup')",
                name="ck_legal_doc_slug_allowed",
            ),
            sa.UniqueConstraint("slug", "version", name="uq_legal_doc_slug_version"),
        )
        op.create_index(
            "ix_legal_doc_slug_current",
            "legal_documents",
            ["slug", "is_current"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    for table_name in (
        "legal_documents",
        "university_leads",
        "data_deletion_requests",
        "data_export_requests",
        "consent_audit_log",
    ):
        if _has_table(inspector, table_name):
            op.drop_table(table_name)

    for col in (
        "lead_score_updated_at",
        "lead_score",
        "referral_source",
        "github_url",
        "linkedin_url",
        "years_work_experience",
        "current_job_title",
        "current_employer",
        "household_income_band",
        "father_occupation",
        "whatsapp_e164",
        "phone_e164",
    ):
        if _has_column(inspector, "student_profiles", col):
            op.drop_column("student_profiles", col)

    for col in (
        "date_of_birth",
        "parent_consent_at",
        "parent_consent_email",
        "account_deleted_at",
        "gdpr_erasure_requested_at",
        "b2b_share_consent_at",
        "b2b_share_consent",
        "marketing_consent",
        "data_consent_user_agent",
        "data_consent_ip",
        "data_consent_granted_at",
        "data_consent_version",
    ):
        if _has_column(inspector, "users", col):
            op.drop_column("users", col)
