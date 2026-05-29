import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app


@pytest.fixture
def app():
    application = create_app()
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Postgres-backed transactional fixtures (E6 keystone)
# Skip cleanly when TEST_DATABASE_URL is absent so unit tests are unaffected.
# ---------------------------------------------------------------------------
import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.database import Base, get_db
import importlib as _importlib
_importlib.import_module("app.models.models")  # noqa: F401  ensure all tables register on Base.metadata

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
requires_db = pytest.mark.skipif(
    TEST_DATABASE_URL is None, reason="requires TEST_DATABASE_URL (Postgres)"
)


def _deduplicate_metadata_indexes(metadata) -> None:
    """Remove duplicate index objects from SQLAlchemy metadata tables.

    Some models define index=True on a column AND also list the same index
    name in __table_args__, producing two Index objects with the same name.
    Postgres raises DuplicateTableError when create_all tries to issue both
    CREATE INDEX statements.  We deduplicate in-memory (no app code touched).
    """
    for table in metadata.tables.values():
        seen: set[str] = set()
        dupes: list = []
        for idx in list(table.indexes):
            if idx.name in seen:
                dupes.append(idx)
            else:
                seen.add(idx.name)
        for idx in dupes:
            table.indexes.discard(idx)


# Fallback isolation strategy: per-test create_all / drop_all.
# The transactional savepoint recipe is incompatible with pytest-asyncio 1.3.0
# when session-scoped and function-scoped fixtures use different event loops.
# Per-test schema creation is slower but provides correct isolation.

@pytest_asyncio.fixture
async def db_session():
    _deduplicate_metadata_indexes(Base.metadata)
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    from sqlalchemy.ext.asyncio import async_sessionmaker
    _session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = _session_factory()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def app_client(db_session):
    application = create_app()

    async def _override_get_db():
        yield db_session

    application.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    application.dependency_overrides.clear()
