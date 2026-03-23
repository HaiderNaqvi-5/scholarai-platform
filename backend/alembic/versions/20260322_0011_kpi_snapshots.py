"""add kpi snapshot tables

Revision ID: 20260322_0011
Revises: 20260321_0010
Create Date: 2026-03-22 01:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260322_0011"
down_revision: Union[str, None] = "20260321_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_kpi_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("kpi_passed", sa.Boolean(), nullable=False),
        sa.Column("metrics_payload", sa.JSON(), nullable=False),
        sa.Column("gates_payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_kpi_snapshots_user_created_at",
        "recommendation_kpi_snapshots",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_kpi_snapshots_policy_version",
        "recommendation_kpi_snapshots",
        ["policy_version"],
        unique=False,
    )

    op.create_table(
        "document_kpi_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("kpi_passed", sa.Boolean(), nullable=False),
        sa.Column("metrics_payload", sa.JSON(), nullable=False),
        sa.Column("gate_payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_kpi_snapshots_user_created_at",
        "document_kpi_snapshots",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_document_kpi_snapshots_document_id",
        "document_kpi_snapshots",
        ["document_id"],
        unique=False,
    )

    op.create_table(
        "interview_kpi_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("kpi_passed", sa.Boolean(), nullable=False),
        sa.Column("metrics_payload", sa.JSON(), nullable=False),
        sa.Column("gate_payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_interview_kpi_snapshots_user_created_at",
        "interview_kpi_snapshots",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_interview_kpi_snapshots_session_id",
        "interview_kpi_snapshots",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_interview_kpi_snapshots_session_id", table_name="interview_kpi_snapshots")
    op.drop_index("ix_interview_kpi_snapshots_user_created_at", table_name="interview_kpi_snapshots")
    op.drop_table("interview_kpi_snapshots")

    op.drop_index("ix_document_kpi_snapshots_document_id", table_name="document_kpi_snapshots")
    op.drop_index("ix_document_kpi_snapshots_user_created_at", table_name="document_kpi_snapshots")
    op.drop_table("document_kpi_snapshots")

    op.drop_index(
        "ix_recommendation_kpi_snapshots_policy_version",
        table_name="recommendation_kpi_snapshots",
    )
    op.drop_index(
        "ix_recommendation_kpi_snapshots_user_created_at",
        table_name="recommendation_kpi_snapshots",
    )
    op.drop_table("recommendation_kpi_snapshots")
