"""add composite index for public scholarship catalog filtering

Backs the SQL-pushed public catalog query in ``list_scholarships``
(``record_state`` + ``country_code`` + ``deadline_at`` range/sort). Replaces
the in-Python full-table scan + slice that previously loaded every published
row into ORM objects before filtering and paginating.

Revision ID: 20260604_0034
Revises: 20260603_0033
Create Date: 2026-06-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260604_0034"
down_revision: Union[str, None] = "20260603_0033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_scholarships_catalog_filter",
        "scholarships",
        ["record_state", "country_code", "deadline_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_scholarships_catalog_filter", table_name="scholarships")
