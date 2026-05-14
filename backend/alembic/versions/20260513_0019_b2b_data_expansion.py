"""b2b data expansion: surface ORM-only columns + add university FKs, GMAT/SAT, budget

Revision ID: 20260513_0019
Revises: 20260511_0018
Create Date: 2026-05-13 21:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260513_0019"
down_revision: Union[str, None] = "20260511_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    new_columns = [
        ("current_university_id", sa.Column("current_university_id", postgresql.UUID(as_uuid=True), nullable=True)),
        ("target_university_ids", sa.Column(
            "target_university_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default=sa.text("ARRAY[]::uuid[]"),
        )),
        ("gmat_score", sa.Column("gmat_score", sa.Integer(), nullable=True)),
        ("sat_score", sa.Column("sat_score", sa.Integer(), nullable=True)),
        ("budget_pkr_max", sa.Column("budget_pkr_max", sa.Integer(), nullable=True)),
    ]

    for name, column in new_columns:
        if not _has_column(inspector, "student_profiles", name):
            op.add_column("student_profiles", column)

    # Constraints: numeric ranges
    op.execute(
        "ALTER TABLE student_profiles "
        "ADD CONSTRAINT ck_student_profiles_gmat_range "
        "CHECK (gmat_score IS NULL OR (gmat_score BETWEEN 200 AND 800))"
    )
    op.execute(
        "ALTER TABLE student_profiles "
        "ADD CONSTRAINT ck_student_profiles_sat_range "
        "CHECK (sat_score IS NULL OR (sat_score BETWEEN 400 AND 1600))"
    )
    op.execute(
        "ALTER TABLE student_profiles "
        "ADD CONSTRAINT ck_student_profiles_budget_nonneg "
        "CHECK (budget_pkr_max IS NULL OR budget_pkr_max >= 0)"
    )

    # FK to universities
    bind.execute(sa.text(
        "ALTER TABLE student_profiles "
        "ADD CONSTRAINT fk_student_profiles_current_university "
        "FOREIGN KEY (current_university_id) REFERENCES universities(id) "
        "ON DELETE SET NULL"
    ))

    if not _has_index(inspector, "student_profiles", "ix_student_profiles_current_university_id"):
        op.create_index(
            "ix_student_profiles_current_university_id",
            "student_profiles",
            ["current_university_id"],
        )

    # GIN index for shortlist membership queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_student_profiles_target_university_ids "
        "ON student_profiles USING GIN (target_university_ids)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_student_profiles_target_university_ids")
    op.execute("DROP INDEX IF EXISTS ix_student_profiles_current_university_id")
    op.execute("ALTER TABLE student_profiles DROP CONSTRAINT IF EXISTS fk_student_profiles_current_university")
    op.execute("ALTER TABLE student_profiles DROP CONSTRAINT IF EXISTS ck_student_profiles_budget_nonneg")
    op.execute("ALTER TABLE student_profiles DROP CONSTRAINT IF EXISTS ck_student_profiles_sat_range")
    op.execute("ALTER TABLE student_profiles DROP CONSTRAINT IF EXISTS ck_student_profiles_gmat_range")
    op.execute("ALTER TABLE student_profiles DROP COLUMN IF EXISTS budget_pkr_max")
    op.execute("ALTER TABLE student_profiles DROP COLUMN IF EXISTS sat_score")
    op.execute("ALTER TABLE student_profiles DROP COLUMN IF EXISTS gmat_score")
    op.execute("ALTER TABLE student_profiles DROP COLUMN IF EXISTS target_university_ids")
    op.execute("ALTER TABLE student_profiles DROP COLUMN IF EXISTS current_university_id")
