"""add mentor to user_role enum

Revision ID: 20260317_0005
Revises: 20260317_0004
Create Date: 2026-03-17
"""
from alembic import op

revision = "20260317_0005"
down_revision = "20260317_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'mentor'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values.
    pass
