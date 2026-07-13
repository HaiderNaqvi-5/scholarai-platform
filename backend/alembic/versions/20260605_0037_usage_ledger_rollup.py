"""Usage-ledger monthly rollup table + period-first prune/read index.

Adds usage_ledger_monthly_summary (one row per user/period) populated by
tasks.run_usage_ledger_rollup, and ix_usage_ledger_period_user serving the
period-then-user scan that month_to_date_pkr and the rollup prune perform.

Note: the spec (R7-NO-LEDGER-RESET) drafted this as revision 20260603_0032 /
down 20260601_0031, but both ids were already taken on disk (the embedding
source-hash migration is 20260603_0032; the legal-slug widen is 20260601_0031).
Chained off the real disk head 20260605_0036 instead so the revision graph
stays a single linear head.

Revision ID: 20260605_0037
Revises: 20260605_0036
Create Date: 2026-06-04 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260605_0037"
down_revision: Union[str, None] = "20260605_0036"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usage_ledger_monthly_summary",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_yyyymm", sa.String(length=6), nullable=False),
        sa.Column("cost_pkr_micro", sa.BigInteger(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id", "period_yyyymm", name="uq_usage_summary_user_period"
        ),
    )
    op.create_index(
        "ix_usage_ledger_period_user",
        "usage_ledger",
        ["period_yyyymm", "user_id"],
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_usage_ledger_period_user")
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "usage_ledger_monthly_summary" in insp.get_table_names():
        op.drop_table("usage_ledger_monthly_summary")
