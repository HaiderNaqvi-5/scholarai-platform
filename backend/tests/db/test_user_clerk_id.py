import pytest
from sqlalchemy import select
from app.models.models import User


def test_user_has_clerk_user_id_column(db_session):
    user = User(
        email="t@example.com",
        password_hash="x",
        full_name="Test",
        clerk_user_id="user_2abc",
    )
    db_session.add(user)
    db_session.commit()
    fetched = db_session.execute(
        select(User).where(User.clerk_user_id == "user_2abc")
    ).scalar_one()
    assert fetched.email == "t@example.com"


def test_clerk_user_id_unique(db_session):
    db_session.add(User(
        email="a@x.com", password_hash="x", full_name="A", clerk_user_id="user_dup",
    ))
    db_session.commit()
    db_session.add(User(
        email="b@x.com", password_hash="x", full_name="B", clerk_user_id="user_dup",
    ))
    with pytest.raises(Exception):
        db_session.commit()
