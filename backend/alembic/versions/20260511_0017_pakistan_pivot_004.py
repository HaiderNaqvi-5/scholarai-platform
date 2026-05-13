"""pakistan pivot 004: visa_interview_questions + visa fields on interview_sessions

Revision ID: 20260511_0017
Revises: 20260511_0016
Create Date: 2026-05-11 18:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260511_0017"
down_revision: Union[str, None] = "20260511_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_table(inspector, "visa_interview_questions"):
        op.create_table(
            "visa_interview_questions",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("country", sa.String(2), nullable=False),
            sa.Column("visa_type", sa.String(32), nullable=False),
            sa.Column("category", sa.String(32), nullable=False),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("ideal_answer_notes", sa.Text(), nullable=True),
            sa.Column(
                "difficulty",
                sa.String(8),
                nullable=False,
                server_default="medium",
            ),
            sa.Column(
                "is_active",
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
                "difficulty IN ('easy','medium','hard')",
                name="ck_visa_q_difficulty_allowed",
            ),
        )
        op.create_index(
            "ix_visa_q_country_visa_active",
            "visa_interview_questions",
            ["country", "visa_type", "is_active"],
        )

    # interview_sessions: add Pakistan visa context columns (additive).
    for col_name, col_type in (
        ("country", sa.String(2)),
        ("visa_type", sa.String(32)),
    ):
        if _has_table(inspector, "interview_sessions") and not _has_column(
            inspector, "interview_sessions", col_name
        ):
            op.add_column("interview_sessions", sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if _has_table(inspector, "interview_sessions"):
        for col_name in ("visa_type", "country"):
            if _has_column(inspector, "interview_sessions", col_name):
                op.drop_column("interview_sessions", col_name)
    if _has_table(inspector, "visa_interview_questions"):
        op.drop_index("ix_visa_q_country_visa_active", table_name="visa_interview_questions")
        op.drop_table("visa_interview_questions")
