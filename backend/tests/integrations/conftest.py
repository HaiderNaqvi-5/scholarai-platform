# Re-export the synchronous SQLite in-memory fixtures so that integration
# tests that need a real DB session (e.g. clerk user-sync tests) can use
# the same fixture defined in tests/db/conftest.py.
from tests.db.conftest import db_engine, db_session  # noqa: F401
