"""add scholarship category column

Revision ID: 20260321_0007
Revises: 20260319_0007
Create Date: 2026-03-21 12:18:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0007"
down_revision = "20260319_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scholarships", sa.Column("category", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("scholarships", "category")
