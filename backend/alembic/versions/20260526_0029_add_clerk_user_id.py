"""add clerk_user_id to users

Revision ID: 20260526_0029
Revises: 20260525_0028
Create Date: 2026-05-26 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260526_0029"
down_revision: Union[str, None] = "20260525_0028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("clerk_user_id", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_users_clerk_user_id", "users", ["clerk_user_id"]
    )
    op.create_index(
        "ix_users_clerk_user_id", "users", ["clerk_user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_users_clerk_user_id", table_name="users")
    op.drop_constraint("uq_users_clerk_user_id", "users", type_="unique")
    op.drop_column("users", "clerk_user_id")
