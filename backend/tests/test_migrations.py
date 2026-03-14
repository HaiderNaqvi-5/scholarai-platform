from pathlib import Path

from app.core.migrations import to_sync_database_url


def test_to_sync_database_url_converts_asyncpg():
    url = "postgresql+asyncpg://scholarai:password@localhost:5432/scholarai"
    assert to_sync_database_url(url) == "postgresql+psycopg2://scholarai:password@localhost:5432/scholarai"


def test_to_sync_database_url_leaves_sync_url_unchanged():
    url = "postgresql+psycopg2://scholarai:password@localhost:5432/scholarai"
    assert to_sync_database_url(url) == url


def test_alembic_scaffold_exists():
    backend_root = Path(__file__).resolve().parents[1]

    assert (backend_root / "alembic" / "env.py").exists()
    assert (backend_root / "alembic" / "script.py.mako").exists()
    assert (backend_root / "alembic" / "versions" / "001_init_schema.py").exists()
