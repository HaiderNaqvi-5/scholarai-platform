"""Add scholarship discovery funding fields

Revision ID: 20260316_0003
Revises: 20260316_0002
Create Date: 2026-03-16 23:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_0003"
down_revision = "20260316_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scholarships", sa.Column("funding_type", sa.String(length=64), nullable=True))
    op.add_column("scholarships", sa.Column("funding_amount_min", sa.Numeric(12, 2), nullable=True))
    op.add_column("scholarships", sa.Column("funding_amount_max", sa.Numeric(12, 2), nullable=True))
    op.create_index(
        "ix_scholarships_funding_type",
        "scholarships",
        ["funding_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_scholarships_funding_type", table_name="scholarships")
    op.drop_column("scholarships", "funding_amount_max")
    op.drop_column("scholarships", "funding_amount_min")
    op.drop_column("scholarships", "funding_type")
