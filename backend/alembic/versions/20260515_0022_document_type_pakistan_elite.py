"""document_type enum: add professor_email + strategy_report (Elite features)

Revision ID: 20260515_0022
Revises: 20260514_0021
Create Date: 2026-05-15 16:10:00

PRD §0.6 Elite-exclusive features persist their output as DocumentRecord rows.
Adds two values to the existing native ``document_type`` PG enum. ADD VALUE is
idempotent via IF NOT EXISTS (PostgreSQL 12+). PG enum values cannot be
removed, so downgrade is a no-op.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260515_0022"
down_revision: Union[str, None] = "20260514_0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'professor_email'")
    op.execute("ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'strategy_report'")
    op.execute("ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'interview_transcript'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values. No-op.
    pass
