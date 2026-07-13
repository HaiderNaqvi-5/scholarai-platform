"""Add ForeignKey + index to ReferralEnrollment.university_id (P2-8).

university_id was a bare UUID column with no referential integrity and no
index, so joins/filters against universities were unenforced and unindexed.
Nulls out any orphaned rows first (values with no matching universities.id)
so the new FK can be added safely, then adds the FK + supporting index.

Revision ID: 20260609_0040
Revises: 20260609_0039
Create Date: 2026-06-09 00:40:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260609_0040"
down_revision: Union[str, None] = "20260609_0039"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_NAME = "fk_referral_enrollments_university_id_universities"
INDEX_NAME = "ix_referral_enrollments_university_id"


def upgrade() -> None:
    # Guard: null out orphan references before adding the FK constraint.
    op.execute(
        "UPDATE referral_enrollments SET university_id = NULL "
        "WHERE university_id IS NOT NULL "
        "AND university_id NOT IN (SELECT id FROM universities)"
    )
    op.create_foreign_key(
        FK_NAME,
        "referral_enrollments",
        "universities",
        ["university_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(INDEX_NAME, "referral_enrollments", ["university_id"])


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="referral_enrollments")
    op.drop_constraint(FK_NAME, "referral_enrollments", type_="foreignkey")
