"""widen legal_documents slug CHECK to include dpa + refund

The b2b_data_use -> dpa rename and the new refund document (legal slug drift
fix) were applied in app code + seeders, but no migration ever updated
``ck_legal_doc_slug_allowed``. Production therefore rejected inserts of the
'dpa' and 'refund' slugs (IntegrityError), leaving legal_documents empty.
This widens the allowlist to the current code's slug set.

Revision ID: 20260601_0031
Revises: 20260601_0030
Create Date: 2026-06-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260601_0031"
down_revision: Union[str, None] = "20260601_0030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE legal_documents DROP CONSTRAINT IF EXISTS ck_legal_doc_slug_allowed")
    op.execute(
        "ALTER TABLE legal_documents ADD CONSTRAINT ck_legal_doc_slug_allowed "
        "CHECK (slug IN ('terms', 'privacy', 'cookies', 'dpa', 'refund', 'aup', 'b2b_data_use'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE legal_documents DROP CONSTRAINT IF EXISTS ck_legal_doc_slug_allowed")
    op.execute(
        "ALTER TABLE legal_documents ADD CONSTRAINT ck_legal_doc_slug_allowed "
        "CHECK (slug IN ('terms', 'privacy', 'cookies', 'b2b_data_use', 'aup'))"
    )
