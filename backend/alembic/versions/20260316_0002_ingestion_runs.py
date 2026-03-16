"""Add ingestion run tracking

Revision ID: 20260316_0002
Revises: 20260316_0001
Create Date: 2026-03-16 22:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260316_0002"
down_revision = "20260316_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    ingestion_run_status = postgresql.ENUM(
        "queued",
        "running",
        "completed",
        "partial",
        "failed",
        name="ingestion_run_status",
        create_type=False,
    )
    ingestion_run_status.create(bind, checkfirst=True)

    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_registry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("triggered_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", ingestion_run_status, nullable=False),
        sa.Column("fetch_url", sa.Text(), nullable=False),
        sa.Column("capture_mode", sa.String(length=32), nullable=True),
        sa.Column("parser_name", sa.String(length=64), nullable=True),
        sa.Column("records_found", sa.Integer(), nullable=False),
        sa.Column("records_created", sa.Integer(), nullable=False),
        sa.Column("records_skipped", sa.Integer(), nullable=False),
        sa.Column("run_metadata", sa.JSON(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_registry_id"], ["source_registry.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["triggered_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_runs_source_created_at",
        "ingestion_runs",
        ["source_registry_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_ingestion_runs_status", "ingestion_runs", ["status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_ingestion_runs_status", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_source_created_at", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
    postgresql.ENUM(name="ingestion_run_status").drop(bind, checkfirst=True)
