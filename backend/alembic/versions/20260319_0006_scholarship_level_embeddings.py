"""add scholarship-level pgvector support for published retrieval

Revision ID: 20260319_0006
Revises: 20260317_0005
Create Date: 2026-03-19 22:45:00
"""

from alembic import op
import sqlalchemy as sa
import pgvector


revision = "20260319_0006"
down_revision = "20260317_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("scholarships")}

    if "description_embedding" not in column_names:
        op.add_column(
            "scholarships",
            sa.Column("description_embedding", pgvector.sqlalchemy.Vector(dim=768), nullable=True),
        )

    # Build the ANN index outside the transaction to avoid long write blocking.
    with op.get_context().autocommit_block():
        op.execute(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS
            ix_scholarships_description_embedding_published
            ON scholarships
            USING ivfflat (description_embedding vector_cosine_ops)
            WITH (lists = 100)
            WHERE record_state = 'published'::scholarship_record_state
              AND description_embedding IS NOT NULL
            """
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            """
            DROP INDEX CONCURRENTLY IF EXISTS
            ix_scholarships_description_embedding_published
            """
        )

    op.drop_column("scholarships", "description_embedding")
