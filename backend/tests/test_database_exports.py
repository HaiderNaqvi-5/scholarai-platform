from app.core import database


def test_session_factory_aliases_are_consistent():
    assert database.async_session_factory is database.async_session
    assert database.AsyncSessionLocal is database.async_session_factory
