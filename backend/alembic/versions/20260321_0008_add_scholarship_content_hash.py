"""add scholarship content hash column

Revision ID: 20260321_0008
Revises: 20260321_0007
Create Date: 2026-03-21 12:42:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0008"
down_revision = "20260321_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scholarships", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.create_index("ix_scholarships_content_hash", "scholarships", ["content_hash"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scholarships_content_hash", table_name="scholarships")
    op.drop_column("scholarships", "content_hash")
