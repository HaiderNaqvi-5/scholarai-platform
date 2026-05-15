"""SOP monthly usage counter + free-tier lifetime counter.

Q1 retier introduces per-plan SOP caps: Free=1 lifetime, Pro=5/mo, Elite=10/mo.
Adds users.lifetime_sop_count (free tier) and sop_monthly_usage(user_id, period_yyyymm)
for paid tiers. Period is YYYYMM string so a simple primary key + upsert handles
monthly rollover without partitioning.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260516_0024"
down_revision = "20260516_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("lifetime_sop_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "sop_monthly_usage",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("period_yyyymm", sa.String(length=6), primary_key=True),
        sa.Column("sop_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "sop_monthly_usage" in insp.get_table_names():
        op.drop_table("sop_monthly_usage")
    cols = {c["name"] for c in insp.get_columns("users")}
    if "lifetime_sop_count" in cols:
        op.drop_column("users", "lifetime_sop_count")
