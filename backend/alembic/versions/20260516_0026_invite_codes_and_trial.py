"""Invite codes + Air University cohort fields + marketing opt-in.

Adds the ``invite_codes`` table (shared-code redemption with use-count,
validity window, and per-cohort plan grant) and five new ``users`` columns:

* ``air_uni_uni`` / ``air_uni_dept`` / ``air_uni_batch`` — optional cohort
  metadata captured at signup so future case-study filtering by university,
  department, and intake year works without a backfill.
* ``redeemed_invite_code`` — denormalised FK-by-value to ``invite_codes.code``
  so a single index supports "which cohort is this user from" queries
  without a join. Indexed for the Day-31 trial-expiry analytics queries.

``users.plan_expires_at`` already shipped in migration ``0024`` — do NOT
re-add here. ``users.marketing_consent`` already exists from the Pakistan
pivot (Feature 9.5) and serves the same purpose as the originally planned
``marketing_opt_in`` — reuse it rather than duplicate. ``invite_codes``
carries no FK back to a single user (it is a shared, counter-incremented
code), so the redemption relationship is expressed entirely via
``users.redeemed_invite_code``.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260516_0026"
down_revision = "20260516_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invite_codes",
        sa.Column("code", sa.String(length=32), primary_key=True),
        sa.Column("cohort", sa.String(length=32), nullable=False),
        sa.Column("grants_plan", sa.String(length=16), nullable=False),
        sa.Column("trial_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("max_uses", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_invite_codes_cohort", "invite_codes", ["cohort"])

    op.add_column("users", sa.Column("air_uni_uni", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("air_uni_dept", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("air_uni_batch", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("redeemed_invite_code", sa.String(length=32), nullable=True))
    op.create_index("ix_users_redeemed_invite_code", "users", ["redeemed_invite_code"])


def downgrade() -> None:
    op.drop_index("ix_users_redeemed_invite_code", table_name="users")
    op.drop_column("users", "redeemed_invite_code")
    op.drop_column("users", "air_uni_batch")
    op.drop_column("users", "air_uni_dept")
    op.drop_column("users", "air_uni_uni")
    op.drop_index("ix_invite_codes_cohort", table_name="invite_codes")
    op.drop_table("invite_codes")
