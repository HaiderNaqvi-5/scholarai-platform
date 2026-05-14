"""ingestion caching + feed table: ETag/Last-Modified + source_feed registry

Revision ID: 20260514_0020
Revises: 20260513_0019
Create Date: 2026-05-14 01:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260514_0020"
down_revision: Union[str, None] = "20260513_0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


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

    if not _has_table(inspector, "source_feed"):
        op.create_table(
            "source_feed",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "source_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("source_registry.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("feed_url", sa.String(2048), nullable=False),
            sa.Column("feed_type", sa.String(16), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "source_id",
                "feed_url",
                name="uq_source_feed_source_url",
            ),
        )
        op.create_index(
            "ix_source_feed_source_id",
            "source_feed",
            ["source_id"],
        )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_source_feed_source_id")
    op.execute("DROP TABLE IF EXISTS source_feed")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS discover_feeds")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS crawl_delay_seconds")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS last_modified")
    op.execute("ALTER TABLE source_registry DROP COLUMN IF EXISTS last_etag")
