"""pakistan pivot 001: plan/billing on users, pakistan profile fields,
target_countries[], waitlist + institution_students + referral_enrollments

Revision ID: 20260511_0014
Revises: 20260328_0013
Create Date: 2026-05-11 16:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260511_0014"
down_revision: Union[str, None] = "20260328_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # --- users: plan / billing scaffolding -------------------------------
    if not _has_column(inspector, "users", "plan"):
        op.add_column(
            "users",
            sa.Column(
                "plan",
                sa.String(16),
                nullable=False,
                server_default="free",
            ),
        )
        op.create_check_constraint(
            "ck_users_plan_allowed",
            "users",
            "plan IN ('free', 'pro', 'elite', 'institution')",
        )
    if not _has_column(inspector, "users", "plan_activated_at"):
        op.add_column(
            "users",
            sa.Column("plan_activated_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not _has_column(inspector, "users", "plan_expires_at"):
        op.add_column(
            "users",
            sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not _has_column(inspector, "users", "plan_currency"):
        op.add_column(
            "users",
            sa.Column(
                "plan_currency",
                sa.String(8),
                nullable=False,
                server_default="PKR",
            ),
        )
    if not _has_column(inspector, "users", "billing_country"):
        op.add_column(
            "users",
            sa.Column("billing_country", sa.String(2), nullable=True),
        )

    # --- DegreeLevel enum: add PHD / MBA / MENG --------------------------
    # Postgres requires ALTER TYPE ... ADD VALUE statements (non-transactional in older versions).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE degree_level ADD VALUE IF NOT EXISTS 'PHD'")
        op.execute("ALTER TYPE degree_level ADD VALUE IF NOT EXISTS 'MBA'")
        op.execute("ALTER TYPE degree_level ADD VALUE IF NOT EXISTS 'MENG'")

    # --- student_profiles: Pakistan-specific fields ----------------------
    pakistan_profile_columns = [
        ("hec_degree_level", sa.String(32)),
        ("pakistani_university", sa.String(120)),
        ("cgpa_scale_choice", sa.String(16)),
        ("degree_subject", sa.String(120)),
        ("graduation_year", sa.Integer()),
        ("toefl_score", sa.Integer()),
        ("ielts_score", sa.Numeric(4, 1)),
        ("gre_quant", sa.Integer()),
        ("gre_verbal", sa.Integer()),
        ("has_research_publications", sa.Boolean(), False),
        ("research_publication_count", sa.Integer(), 0),
        ("funding_requirement", sa.String(32)),
        ("intake_target", sa.String(32)),
        ("city_of_origin", sa.String(120)),
        ("can_afford_application_fees", sa.Boolean(), None),
        ("needs_gre_waiver", sa.Boolean(), None),
        ("family_has_funds_for_bank_statement", sa.Boolean(), None),
    ]
    for entry in pakistan_profile_columns:
        if len(entry) == 2:
            name, sa_type = entry
            default = None
        else:
            name, sa_type, default = entry
        if not _has_column(inspector, "student_profiles", name):
            kwargs = {"nullable": True}
            if default is not None:
                kwargs["server_default"] = sa.text(str(default).lower() if isinstance(default, bool) else str(default))
            op.add_column("student_profiles", sa.Column(name, sa_type, **kwargs))

    # target_countries TEXT[] (additive; keep target_country_code column for back-compat)
    if not _has_column(inspector, "student_profiles", "target_countries"):
        op.add_column(
            "student_profiles",
            sa.Column(
                "target_countries",
                postgresql.ARRAY(sa.String(length=2)),
                nullable=False,
                server_default=sa.text("ARRAY[]::varchar[]"),
            ),
        )
        # backfill from existing target_country_code
        op.execute(
            "UPDATE student_profiles "
            "SET target_countries = ARRAY[target_country_code] "
            "WHERE target_country_code IS NOT NULL AND cardinality(target_countries) = 0"
        )

    # target_fields TEXT[]
    if not _has_column(inspector, "student_profiles", "target_fields"):
        op.add_column(
            "student_profiles",
            sa.Column(
                "target_fields",
                postgresql.ARRAY(sa.String(length=64)),
                nullable=False,
                server_default=sa.text("ARRAY[]::varchar[]"),
            ),
        )
        op.execute(
            "UPDATE student_profiles "
            "SET target_fields = ARRAY[target_field] "
            "WHERE target_field IS NOT NULL AND cardinality(target_fields) = 0"
        )

    # --- waitlist table --------------------------------------------------
    if not _has_table(inspector, "waitlist"):
        op.create_table(
            "waitlist",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("email", sa.Text(), nullable=False, unique=True),
            sa.Column(
                "plan",
                sa.String(16),
                nullable=False,
                server_default="pro",
            ),
            sa.Column(
                "currency",
                sa.String(8),
                nullable=False,
                server_default="PKR",
            ),
            sa.Column("country", sa.String(2), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint(
                "plan IN ('pro', 'elite', 'institution')",
                name="ck_waitlist_plan_allowed",
            ),
        )
        op.create_index("ix_waitlist_email", "waitlist", ["email"], unique=True)

    # --- institutions: B2B extensions (additive on existing table) -------
    if not _has_column(inspector, "institutions", "type"):
        op.add_column(
            "institutions",
            sa.Column("type", sa.String(16), nullable=True),
        )
        op.create_check_constraint(
            "ck_institutions_type_allowed",
            "institutions",
            "type IS NULL OR type IN ('school', 'university', 'hec', 'other')",
        )
    for col_name, col_type in (
        ("country", sa.String(2)),
        ("contact_email", sa.Text()),
        ("seat_limit", sa.Integer()),
        ("dpa_signed_at", sa.DateTime(timezone=True)),
    ):
        if not _has_column(inspector, "institutions", col_name):
            op.add_column("institutions", sa.Column(col_name, col_type, nullable=True))

    # --- institution_students --------------------------------------------
    if not _has_table(inspector, "institution_students"):
        op.create_table(
            "institution_students",
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    # --- referral_enrollments --------------------------------------------
    if not _has_table(inspector, "referral_enrollments"):
        op.create_table(
            "referral_enrollments",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "university_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
            sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("fee_usd", sa.Integer(), nullable=True),
            sa.Column("invoiced_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_referral_enrollments_user_id",
            "referral_enrollments",
            ["user_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_table(inspector, "referral_enrollments"):
        op.drop_index("ix_referral_enrollments_user_id", table_name="referral_enrollments")
        op.drop_table("referral_enrollments")
    if _has_table(inspector, "institution_students"):
        op.drop_table("institution_students")

    for col_name in ("dpa_signed_at", "seat_limit", "contact_email", "country", "type"):
        if _has_column(inspector, "institutions", col_name):
            op.drop_column("institutions", col_name)
    op.execute("ALTER TABLE institutions DROP CONSTRAINT IF EXISTS ck_institutions_type_allowed")

    if _has_table(inspector, "waitlist"):
        op.drop_index("ix_waitlist_email", table_name="waitlist")
        op.drop_table("waitlist")

    pakistan_profile_cols = [
        "target_fields",
        "target_countries",
        "family_has_funds_for_bank_statement",
        "needs_gre_waiver",
        "can_afford_application_fees",
        "city_of_origin",
        "intake_target",
        "funding_requirement",
        "research_publication_count",
        "has_research_publications",
        "gre_verbal",
        "gre_quant",
        "ielts_score",
        "toefl_score",
        "graduation_year",
        "degree_subject",
        "cgpa_scale_choice",
        "pakistani_university",
        "hec_degree_level",
    ]
    for col in pakistan_profile_cols:
        if _has_column(inspector, "student_profiles", col):
            op.drop_column("student_profiles", col)

    # DegreeLevel additions: cannot drop enum values cleanly without recreating the type.
    # Leaving PHD/MBA/MENG in place on downgrade is acceptable — rows are nullable on add.

    for col in ("billing_country", "plan_currency", "plan_expires_at", "plan_activated_at"):
        if _has_column(inspector, "users", col):
            op.drop_column("users", col)
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_plan_allowed")
    if _has_column(inspector, "users", "plan"):
        op.drop_column("users", "plan")
