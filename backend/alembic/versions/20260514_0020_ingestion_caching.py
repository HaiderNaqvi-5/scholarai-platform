"""ingestion caching: ETag/Last-Modified + crawl_delay + feed-discovery toggle

Revision ID: 20260514_0020
Revises: 20260513_0019
Create Date: 2026-05-14 01:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260514_0020"
down_revision: Union[str, None] = "20260513_0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    new_columns = [
        ("last_etag", sa.Column("last_etag", sa.String(255), nullable=True)),
        ("last_modified", sa.Column("last_modified", sa.String(64), nullable=True)),
        ("crawl_delay_seconds", sa.Column("crawl_delay_seconds", sa.Float(), nullable=True)),
        (
            "discover_feeds",
            sa.Column(
                "discover_feeds",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        ),
    ]

    for name, column in new_columns:
        if not _has_column(inspector, "source_registry", name):
            op.add_column("source_registry", column)


def downgrade() -> None:
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS discover_feeds")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS crawl_delay_seconds")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS last_modified")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS last_etag")
