"""add scholarship category column

Revision ID: 20260321_0009
Revises: 20260321_0008
Create Date: 2026-03-21 00:00:09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260321_0009"
down_revision: Union[str, None] = "20260321_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    scholarship_columns = {col["name"] for col in inspector.get_columns("scholarships")}

    if "category" not in scholarship_columns:
        op.add_column("scholarships", sa.Column("category", sa.String(length=64), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    scholarship_columns = {col["name"] for col in inspector.get_columns("scholarships")}

    if "category" in scholarship_columns:
        op.drop_column("scholarships", "category")
