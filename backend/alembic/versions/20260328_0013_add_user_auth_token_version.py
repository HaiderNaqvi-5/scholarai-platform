"""add auth token version to users

Revision ID: 20260328_0013
Revises: 20260324_0012
Create Date: 2026-03-28 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260328_0013"
down_revision: Union[str, None] = "20260324_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, "users", "auth_token_version"):
        op.add_column(
            "users",
            sa.Column("auth_token_version", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("users", "auth_token_version", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_column(inspector, "users", "auth_token_version"):
        op.drop_column("users", "auth_token_version")
