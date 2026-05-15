"""Per-user usage ledger for burn-cap (60% revenue) accounting.

Tracks Anthropic LLM calls and notification fan-out cost per user per month.
cost_pkr_micro stores PKR * 1e6 as BigInteger so integer SUM stays exact across
millions of rows. Index on (user_id, period_yyyymm) supports the month-to-date
aggregate query that gates every future LLM call.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260516_0025"
down_revision = "20260516_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usage_ledger",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_yyyymm", sa.String(length=6), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_pkr_micro", sa.BigInteger(), nullable=False),
        sa.Column("endpoint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_usage_ledger_user_period",
        "usage_ledger",
        ["user_id", "period_yyyymm"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "usage_ledger" in insp.get_table_names():
        op.execute("DROP INDEX IF EXISTS ix_usage_ledger_user_period")
        op.drop_table("usage_ledger")
