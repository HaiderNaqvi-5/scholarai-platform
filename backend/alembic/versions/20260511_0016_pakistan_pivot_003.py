"""pakistan pivot 003: application_tracker_items kanban table

Revision ID: 20260511_0016
Revises: 20260511_0015
Create Date: 2026-05-11 17:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260511_0016"
down_revision: Union[str, None] = "20260511_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_table(inspector, "application_tracker_items"):
        op.create_table(
            "application_tracker_items",
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
                "scholarship_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("scholarships.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "university_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("universities.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("program_name", sa.Text(), nullable=True),
            sa.Column("university_name", sa.Text(), nullable=True),
            sa.Column("country", sa.String(2), nullable=True),
            sa.Column(
                "stage",
                sa.String(32),
                nullable=False,
                server_default="researching",
            ),
            sa.Column("deadline", sa.Date(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "document_checklist",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint(
                "stage IN ('researching','preparing','applied','interview','decision','accepted')",
                name="ck_tracker_stage_allowed",
            ),
        )
        op.create_index(
            "ix_tracker_user_stage",
            "application_tracker_items",
            ["user_id", "stage"],
        )
        op.create_index(
            "ix_tracker_user_deadline",
            "application_tracker_items",
            ["user_id", "deadline"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if _has_table(inspector, "application_tracker_items"):
        op.drop_index("ix_tracker_user_deadline", table_name="application_tracker_items")
        op.drop_index("ix_tracker_user_stage", table_name="application_tracker_items")
        op.drop_table("application_tracker_items")
