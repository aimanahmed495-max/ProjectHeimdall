import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.app import models
from backend.app.database import engine, get_db
from backend.app.main import app
from backend.app.security import create_access_token, hash_password


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    session.execute(delete(models.AlertLog))
    session.execute(delete(models.SystemLog))
    session.execute(delete(models.ThreatEvent))
    session.execute(delete(models.CameraState))
    session.execute(delete(models.OsintSource))
    session.execute(delete(models.User))
    session.flush()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def unauthenticated_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    user = models.User(
        username="automated.test.operator",
        password_hash=hash_password("AutomatedTestPassword123!"),
    )
    db_session.add(user)
    db_session.flush()

    token = create_access_token(user.user_id)

    with TestClient(
        app,
        headers={"Authorization": f"Bearer {token}"},
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()
