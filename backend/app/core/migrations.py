from sqlalchemy.engine import make_url


def to_sync_database_url(database_url: str) -> str:
    """Convert async SQLAlchemy URLs into sync URLs for Alembic."""
    url = make_url(database_url)

    if url.drivername == "postgresql+asyncpg":
        url = url.set(drivername="postgresql+psycopg2")

    return url.render_as_string(hide_password=False)
