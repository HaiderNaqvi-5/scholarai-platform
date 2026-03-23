"""add institution scope columns for curation entities

Revision ID: 20260321_0010
Revises: 20260321_0011
Create Date: 2026-03-21 00:00:10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260321_0010"
down_revision: Union[str, None] = "20260321_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if "institution_id" not in _column_names("source_registry"):
        op.add_column(
            "source_registry",
            sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "source_registry_institution_id_fkey",
            "source_registry",
            "institutions",
            ["institution_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index("ix_source_registry_institution_id", "source_registry", ["institution_id"])

    if "institution_id" not in _column_names("ingestion_runs"):
        op.add_column(
            "ingestion_runs",
            sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "ingestion_runs_institution_id_fkey",
            "ingestion_runs",
            "institutions",
            ["institution_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index("ix_ingestion_runs_institution_id", "ingestion_runs", ["institution_id"])

    if "institution_id" not in _column_names("scholarships"):
        op.add_column(
            "scholarships",
            sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "scholarships_institution_id_fkey",
            "scholarships",
            "institutions",
            ["institution_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index("ix_scholarships_institution_id", "scholarships", ["institution_id"])

    op.execute(
        """
        UPDATE scholarships s
        SET institution_id = sr.institution_id
        FROM source_registry sr
        WHERE s.source_registry_id = sr.id
          AND s.institution_id IS NULL
          AND sr.institution_id IS NOT NULL
        """
    )

    op.execute(
        """
        UPDATE ingestion_runs ir
        SET institution_id = sr.institution_id
        FROM source_registry sr
        WHERE ir.source_registry_id = sr.id
          AND ir.institution_id IS NULL
          AND sr.institution_id IS NOT NULL
        """
    )


def downgrade() -> None:
    if "institution_id" in _column_names("scholarships"):
        op.drop_index("ix_scholarships_institution_id", table_name="scholarships")
        op.drop_constraint("scholarships_institution_id_fkey", "scholarships", type_="foreignkey")
        op.drop_column("scholarships", "institution_id")

    if "institution_id" in _column_names("ingestion_runs"):
        op.drop_index("ix_ingestion_runs_institution_id", table_name="ingestion_runs")
        op.drop_constraint("ingestion_runs_institution_id_fkey", "ingestion_runs", type_="foreignkey")
        op.drop_column("ingestion_runs", "institution_id")

    if "institution_id" in _column_names("source_registry"):
        op.drop_index("ix_source_registry_institution_id", table_name="source_registry")
        op.drop_constraint("source_registry_institution_id_fkey", "source_registry", type_="foreignkey")
        op.drop_column("source_registry", "institution_id")
