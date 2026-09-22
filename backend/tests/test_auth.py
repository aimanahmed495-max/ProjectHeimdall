from sqlalchemy import select

from backend.app import models
from backend.app.security import verify_password


VALID_USER = {
    "username": "heimdall.operator",
    "password": "SecurePassword123!",
}


def register_user(client):
    response = client.post(
        "/auth/register",
        json=VALID_USER,
    )
    assert response.status_code == 201
    return response


def login_user(client):
    response = client.post(
        "/auth/login",
        json=VALID_USER,
    )
    assert response.status_code == 200
    return response


def test_register_user_hashes_password(client, db_session):
    response = register_user(client)

    body = response.json()
    assert body["username"] == "heimdall.operator"
    assert body["is_active"] is True
    assert body["deleted_at"] is None
    assert "password" not in body
    assert "password_hash" not in body

    user = db_session.scalar(
        select(models.User).where(models.User.username == "heimdall.operator")
    )

    assert user is not None
    assert user.password_hash != VALID_USER["password"]
    assert verify_password(
        VALID_USER["password"],
        user.password_hash,
    )


def test_duplicate_username_returns_conflict(client):
    register_user(client)

    response = client.post(
        "/auth/register",
        json=VALID_USER,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "A user with this username already exists."


def test_registration_requires_strong_password(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "short.password",
            "password": "too-short",
        },
    )

    assert response.status_code == 422


def test_login_and_get_current_user(client):
    register_user(client)

    login_response = login_user(client)
    token_body = login_response.json()

    assert token_body["token_type"] == "bearer"
    assert token_body["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": (f"Bearer {token_body['access_token']}")},
    )

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "heimdall.operator"


def test_login_rejects_incorrect_password(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "username": VALID_USER["username"],
            "password": "IncorrectPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired authentication credentials."


def test_current_user_requires_bearer_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_current_user_rejects_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_use_existing_token(
    client,
    db_session,
):
    register_user(client)
    token = login_user(client).json()["access_token"]

    user = db_session.scalar(
        select(models.User).where(models.User.username == "heimdall.operator")
    )
    user.is_active = False
    db_session.commit()

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
