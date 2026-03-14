import os
from pathlib import Path
import subprocess
import sys

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


def test_offline_alembic_sql_has_single_enum_definition():
    backend_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["DEBUG"] = "false"

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=backend_root,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.stdout.count("CREATE TYPE user_role") == 1
    assert result.stdout.count("CREATE TYPE degree_level_enum") == 1
    assert "INSERT INTO alembic_version" in result.stdout
