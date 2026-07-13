"""add scholarships.embedding_source_hash for incremental embedding refresh

Stores the sha256 of the refresher's _build_document_text() output so the
embedding refresh can skip scholarships whose document text is unchanged
(incremental re-embed). Distinct from scholarships.content_hash, which is the
ingestion/curation dedup hash of the raw source candidate.

Revision ID: 20260603_0032
Revises: 20260601_0031
Create Date: 2026-06-03 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260603_0032"
down_revision: Union[str, None] = "20260601_0031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scholarships",
        sa.Column("embedding_source_hash", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scholarships", "embedding_source_hash")
