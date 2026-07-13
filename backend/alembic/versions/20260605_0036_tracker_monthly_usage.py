"""tracker_monthly_usage per-(user,month) creation counter

TRACKER_CAP previously gated on a live count(*) of application_tracker_items,
so delete+recreate reset the monthly cap. This table logs each tracker
creation per (user, YYYYMM) so the gate counts creations, not live rows.
Parallel to sop_monthly_usage (rev 20260516_0024).

Note: the spec (R6-TRACKER-CAP) drafted this as revision 20260603_0032 / down
20260601_0031, but both ids were already taken on disk (the embedding
source-hash migration is 20260603_0032; the legal-slug widen is 20260601_0031).
Chained off the real disk head 20260605_0035 instead so the revision graph
stays a single linear head.

Revision ID: 20260605_0036
Revises: 20260605_0035
Create Date: 2026-06-04 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260605_0036"
down_revision: Union[str, None] = "20260605_0035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tracker_monthly_usage",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("period_yyyymm", sa.String(length=6), primary_key=True),
        sa.Column(
            "created_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "tracker_monthly_usage" in insp.get_table_names():
        op.drop_table("tracker_monthly_usage")
