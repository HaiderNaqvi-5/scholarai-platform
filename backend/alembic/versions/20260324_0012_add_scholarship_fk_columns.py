"""add missing scholarship foreign keys to documents and interview sessions

Revision ID: 20260324_0012
Revises: 20260322_0011
Create Date: 2026-03-24 05:08:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260324_0012"
down_revision: Union[str, None] = "20260322_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_fk(inspector, table_name: str, fk_name: str) -> bool:
    return any(fk["name"] == fk_name for fk in inspector.get_foreign_keys(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, "documents", "scholarship_id"):
        op.add_column(
            "documents",
            sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_documents_scholarship_id_scholarships",
            "documents",
            "scholarships",
            ["scholarship_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not _has_column(inspector, "interview_sessions", "scholarship_id"):
        op.add_column(
            "interview_sessions",
            sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_interview_sessions_scholarship_id_scholarships",
            "interview_sessions",
            "scholarships",
            ["scholarship_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_fk(inspector, "interview_sessions", "fk_interview_sessions_scholarship_id_scholarships"):
        op.drop_constraint(
            "fk_interview_sessions_scholarship_id_scholarships",
            "interview_sessions",
            type_="foreignkey",
        )
    if _has_column(inspector, "interview_sessions", "scholarship_id"):
        op.drop_column("interview_sessions", "scholarship_id")

    if _has_fk(inspector, "documents", "fk_documents_scholarship_id_scholarships"):
        op.drop_constraint(
            "fk_documents_scholarship_id_scholarships",
            "documents",
            type_="foreignkey",
        )
    if _has_column(inspector, "documents", "scholarship_id"):
        op.drop_column("documents", "scholarship_id")
