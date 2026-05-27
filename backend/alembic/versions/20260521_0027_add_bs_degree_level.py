"""Add BS to degree_level enum.

Revision ID: 20260521_0027
Revises: 20260516_0026
Create Date: 2026-05-21
"""

revision = "20260521_0027"
down_revision = "20260516_0026"
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.execute("ALTER TYPE degree_level ADD VALUE IF NOT EXISTS 'BS'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; downgrade is a no-op.
    pass
