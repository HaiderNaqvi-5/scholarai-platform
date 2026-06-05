"""scholarship match candidate composite partial index (perf-db-02)

POST /scholarships/match now pushes record_state/tier/country_code/min_gpa
hard filters + an ORDER BY deadline_at + LIMIT into SQL. This composite
partial index (published rows only) serves that bounded candidate scan from a
single index instead of a seq-scan + sort over the whole published table.

Note: the spec drafted this as revision 20260603_0032 / down 20260601_0031, but
both ids were already taken on disk (the embedding-source-hash and legal-slug
migrations). Chained off the real disk head 20260604_0034 instead so the
revision graph stays a single linear head.

Revision ID: 20260605_0035
Revises: 20260604_0034
Create Date: 2026-06-05 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260605_0035"
down_revision: Union[str, None] = "20260604_0034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_scholarships_match_candidate",
        "scholarships",
        ["country_code", "deadline_at", "min_gpa_value"],
        unique=False,
        postgresql_where=sa.text(
            "record_state = 'published'::scholarship_record_state"
        ),
    )


def downgrade() -> None:
    op.drop_index("ix_scholarships_match_candidate", table_name="scholarships")
