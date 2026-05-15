"""scholarship tier (standard/premium) for Q1 retier."""
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
        "WHERE LOWER(name) ~ "
        "'(chevening|fulbright|daad|commonwealth|hec overseas|rhodes|gates|schwarzman|erasmus mundus)' "
        "OR LOWER(provider) ~ "
        "'(chevening|fulbright|daad|commonwealth|hec|rhodes|gates foundation|schwarzman|erasmus)'"
    )


def downgrade() -> None:
    op.drop_index("ix_scholarships_tier", table_name="scholarships")
    op.drop_column("scholarships", "tier")
    sa.Enum(name="scholarship_tier").drop(op.get_bind(), checkfirst=True)
