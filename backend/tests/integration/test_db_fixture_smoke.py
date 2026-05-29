import pytest
from sqlalchemy import select

from tests.conftest import requires_db
from app.models.models import User


@requires_db
async def test_db_session_executes_real_sql(db_session):
    user = User(email="probe@test.local", password_hash="x", full_name="Probe User")
    db_session.add(user)
    await db_session.flush()
    fetched = (
        await db_session.execute(select(User).where(User.email == "probe@test.local"))
    ).scalar_one()
    assert fetched.id is not None
    assert fetched.full_name == "Probe User"


@requires_db
async def test_app_client_uses_overridden_db(app_client):
    resp = await app_client.get("/api/v1/health")
    assert resp.status_code == 200
