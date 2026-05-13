"""pakistan pivot 002: universities table with Pakistan-relevant metadata

Revision ID: 20260511_0015
Revises: 20260511_0014
Create Date: 2026-05-11 17:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260511_0015"
down_revision: Union[str, None] = "20260511_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_table(inspector, "universities"):
        op.create_table(
            "universities",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("country", sa.String(2), nullable=False),
            sa.Column("city", sa.String(120), nullable=True),
            sa.Column("website_url", sa.Text(), nullable=True),
            sa.Column(
                "accepts_hec_degrees",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "has_pakistani_alumni_network",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "offers_gta_gra",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column("avg_visa_approval_rate_pk", sa.Float(), nullable=True),
            sa.Column(
                "requires_gre",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "accepts_ielts",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "accepts_toefl",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column("min_ielts_overall", sa.Float(), nullable=True),
            sa.Column("min_ielts_each_band", sa.Float(), nullable=True),
            sa.Column("min_cgpa", sa.Float(), nullable=True),
            sa.Column("application_fee_usd", sa.Integer(), nullable=True),
            sa.Column(
                "application_fee_waiver_available",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "intake_months",
                postgresql.ARRAY(sa.String(length=12)),
                nullable=False,
                server_default=sa.text("ARRAY[]::varchar[]"),
            ),
            sa.Column(
                "fields_offered",
                postgresql.ARRAY(sa.String(length=64)),
                nullable=False,
                server_default=sa.text("ARRAY[]::varchar[]"),
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_universities_country", "universities", ["country"])
        op.create_index("ix_universities_name", "universities", ["name"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if _has_table(inspector, "universities"):
        op.drop_index("ix_universities_name", table_name="universities")
        op.drop_index("ix_universities_country", table_name="universities")
        op.drop_table("universities")
