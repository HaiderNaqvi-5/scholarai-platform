"""add scholarship interview practice mode

Revision ID: 20260319_0007
Revises: 20260319_0006
Create Date: 2026-03-19 23:35:00
"""

from alembic import op


revision = "20260319_0007"
down_revision = "20260319_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'interview_practice_mode'
                  AND e.enumlabel = 'scholarship'
            ) THEN
                ALTER TYPE interview_practice_mode ADD VALUE 'scholarship';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass
