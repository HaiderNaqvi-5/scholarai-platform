"""scholarship tier (standard/premium) for Q1 retier

Revision ID: 20260516_0023
Revises: 20260515_0022
Create Date: 2026-05-16 00:23:00

Adds a native PG ``scholarship_tier`` enum (``standard`` / ``premium``) and a
``tier`` column on ``scholarships`` with a btree index, defaulting every
existing row to ``standard``. This unlocks the Q1 retier work — premium
scholarships get differentiated ranking + UI treatment without polluting the
existing ``record_state`` lifecycle.

The migration also performs a regex backfill of marquee programs (Chevening,
Fulbright, DAAD, Commonwealth, HEC Overseas, Rhodes, Gates, Schwarzman,
Erasmus Mundus) to ``premium`` so the first deploy isn't blocked on a separate
data job. Downgrade is idempotent (``DROP INDEX IF EXISTS`` + inspector-gated
column drop + ``checkfirst=True`` on the enum) so partial rollbacks on shared
environments don't wedge subsequent ``alembic downgrade`` runs.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260516_0023"
down_revision = "20260515_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tier = sa.Enum("standard", "premium", name="scholarship_tier")
    tier.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "scholarships",
        sa.Column("tier", tier, nullable=False, server_default="standard"),
    )
    op.create_index("ix_scholarships_tier", "scholarships", ["tier"])
    op.execute(
        "UPDATE scholarships SET tier = 'premium' "
        "WHERE LOWER(title) ~ "
        "'(chevening|fulbright|daad|commonwealth|hec overseas|rhodes|gates|schwarzman|erasmus mundus)' "
        "OR LOWER(provider_name) ~ "
        "'(chevening|fulbright|daad|commonwealth|hec|rhodes|gates foundation|schwarzman|erasmus)'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_scholarships_tier")
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("scholarships")}
    if "tier" in cols:
        op.drop_column("scholarships", "tier")
    sa.Enum(name="scholarship_tier").drop(op.get_bind(), checkfirst=True)
