"""Drop orphaned description_embedding column + ivfflat index from scholarships.

The column was written by embedding_refresh but never read by retrieval
(chunk-ANN via ScholarshipChunk.embedding is the live path). Removing the
write (embedding_refresh.py) and the schema artefacts (column + index).

Revision ID: 20260609_0038
Revises: 20260605_0037
Create Date: 2026-06-09 00:38:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = "20260609_0038"
down_revision: Union[str, None] = "20260605_0037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        "ix_scholarships_description_embedding_published",
        table_name="scholarships",
    )
    op.drop_column("scholarships", "description_embedding")


def downgrade() -> None:
    op.add_column(
        "scholarships",
        sa.Column(
            "description_embedding",
            Vector(768),
            nullable=True,
        ),
    )
    op.execute(
        "CREATE INDEX ix_scholarships_description_embedding_published"
        " ON scholarships"
        " USING ivfflat (description_embedding vector_cosine_ops)"
        " WITH (lists = 100)"
        " WHERE record_state = 'published'"
        " AND description_embedding IS NOT NULL"
    )
