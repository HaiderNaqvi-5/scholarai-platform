"""add single-column created_at indexes to kpi snapshot tables

Backs the set-based purge in KPISnapshotService._delete_older_than, which runs
``DELETE ... WHERE created_at < cutoff`` per snapshot table. The existing
composite ``ix_*_user_created_at`` indexes lead with ``user_id`` and cannot
serve a ``created_at``-only range predicate efficiently, so a standalone
``created_at`` index is added to each of the three KPI snapshot tables.

Revision ID: 20260603_0033
Revises: 20260603_0032
Create Date: 2026-06-03 00:30:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260603_0033"
down_revision: Union[str, None] = "20260603_0032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_recommendation_kpi_snapshots_created_at",
        "recommendation_kpi_snapshots",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_document_kpi_snapshots_created_at",
        "document_kpi_snapshots",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_interview_kpi_snapshots_created_at",
        "interview_kpi_snapshots",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_interview_kpi_snapshots_created_at",
        table_name="interview_kpi_snapshots",
    )
    op.drop_index(
        "ix_document_kpi_snapshots_created_at",
        table_name="document_kpi_snapshots",
    )
    op.drop_index(
        "ix_recommendation_kpi_snapshots_created_at",
        table_name="recommendation_kpi_snapshots",
    )
