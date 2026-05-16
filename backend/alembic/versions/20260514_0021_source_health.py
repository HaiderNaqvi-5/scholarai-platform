"""source-health monitoring: per-source success/failure heartbeat columns

Revision ID: 20260514_0021
Revises: 20260514_0020
Create Date: 2026-05-14 16:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260514_0021"
down_revision: Union[str, None] = "20260514_0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    new_columns = [
        ("last_success_at", sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True)),
        ("last_failure_at", sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True)),
        (
            "consecutive_failures",
            sa.Column(
                "consecutive_failures",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        ),
        (
            "health_status",
            sa.Column(
                "health_status",
                sa.String(16),
                nullable=False,
                server_default=sa.text("'unknown'"),
            ),
        ),
    ]

    for name, column in new_columns:
        if not _has_column(inspector, "source_registry", name):
            op.add_column("source_registry", column)


def downgrade() -> None:
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS health_status")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS consecutive_failures")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS last_failure_at")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS last_success_at")
