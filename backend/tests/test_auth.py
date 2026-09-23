import pytest
from sqlalchemy import select

from backend.app import models
from backend.app.security import verify_password


VALID_USER = {
    "username": "heimdall.operator",
    "password": "SecurePassword123!",
}


def register_user(unauthenticated_client):
    response = unauthenticated_client.post(
        "/auth/register",
        json=VALID_USER,
    )
    assert response.status_code == 201
    return response


def login_user(unauthenticated_client):
    response = unauthenticated_client.post(
        "/auth/login",
        json=VALID_USER,
    )
    assert response.status_code == 200
    return response


def test_register_user_hashes_password(unauthenticated_client, db_session):
    response = register_user(unauthenticated_client)

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


def test_duplicate_username_returns_conflict(unauthenticated_client):
    register_user(unauthenticated_client)

    response = unauthenticated_client.post(
        "/auth/register",
        json=VALID_USER,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "A user with this username already exists."


def test_registration_requires_strong_password(unauthenticated_client):
    response = unauthenticated_client.post(
        "/auth/register",
        json={
            "username": "short.password",
            "password": "too-short",
        },
    )

    assert response.status_code == 422


def test_login_and_get_current_user(unauthenticated_client):
    register_user(unauthenticated_client)

    login_response = login_user(unauthenticated_client)
    token_body = login_response.json()

    assert token_body["token_type"] == "bearer"
    assert token_body["access_token"]

    me_response = unauthenticated_client.get(
        "/auth/me",
        headers={"Authorization": (f"Bearer {token_body['access_token']}")},
    )

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "heimdall.operator"


def test_login_rejects_incorrect_password(unauthenticated_client):
    register_user(unauthenticated_client)

    response = unauthenticated_client.post(
        "/auth/login",
        json={
            "username": VALID_USER["username"],
            "password": "IncorrectPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired authentication credentials."


def test_current_user_requires_bearer_token(unauthenticated_client):
    response = unauthenticated_client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_current_user_rejects_invalid_token(unauthenticated_client):
    response = unauthenticated_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_use_existing_token(
    unauthenticated_client,
    db_session,
):
    register_user(unauthenticated_client)
    token = login_user(unauthenticated_client).json()["access_token"]

    user = db_session.scalar(
        select(models.User).where(models.User.username == "heimdall.operator")
    )
    user.is_active = False
    db_session.commit()

    response = unauthenticated_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        (
            "post",
            "/sources",
            {
                "source_name": "Protected Source",
                "source_type": "Public API",
                "url": "https://example.com",
                "reliability_score": 0.9,
            },
        ),
        (
            "post",
            "/threat-events",
            {
                "object_class": "person",
                "confidence_score": 0.9,
                "camera_id": 1,
                "status": "Pending",
            },
        ),
        (
            "post",
            "/alert-logs",
            {
                "event_id": 1,
                "alert_level": "Critical",
                "message": "Protected alert",
                "acknowledged": False,
            },
        ),
        (
            "post",
            "/camera-states",
            {
                "camera_id": 1,
                "mode": "Active",
                "fps": 30,
                "resolution": "1080p",
            },
        ),
        (
            "put",
            "/camera-states/1",
            {
                "mode": "Dormant",
                "fps": 5,
                "resolution": "720p",
            },
        ),
        (
            "post",
            "/system-logs",
            {
                "event_id": None,
                "module": "vision",
                "message": "Protected system log",
            },
        ),
    ],
)
def test_write_routes_require_authentication(
    unauthenticated_client,
    method,
    path,
    payload,
):
    response = unauthenticated_client.request(
        method,
        path,
        json=payload,
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_registration_can_be_disabled(
    unauthenticated_client,
    monkeypatch,
):
    monkeypatch.setenv("ENABLE_USER_REGISTRATION", "false")

    response = unauthenticated_client.post(
        "/auth/register",
        json=VALID_USER,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User registration is disabled."
