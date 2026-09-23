from unittest.mock import Mock, call

import pytest

from vision.vision_client import HeimdallAPIError, HeimdallVisionClient


def make_response(status_code, payload):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    response.text = str(payload)
    response.request.method = "GET"
    response.url = "http://localhost:8000/camera-states/1"
    return response


def test_set_camera_state_registers_missing_camera():
    client = HeimdallVisionClient()

    lookup_response = make_response(
        404,
        {"detail": "Camera state not found."},
    )
    created_camera = {
        "state_id": 1,
        "camera_id": 1,
        "mode": "Active",
        "fps": 5,
        "resolution": "720p",
        "timestamp": "2026-09-21T20:00:00Z",
    }
    state = {
        "camera_id": 1,
        "mode": "Active",
        "fps": 5,
        "resolution": "720p",
    }

    client._request = Mock(return_value=lookup_response)
    client.post_camera_state = Mock(return_value=created_camera)

    result = client.set_camera_state(state)

    assert result == created_camera
    client._request.assert_called_once_with(
        "GET",
        "/camera-states/1",
    )
    client.post_camera_state.assert_called_once_with(state)


def test_set_camera_state_updates_existing_camera():
    client = HeimdallVisionClient()

    lookup_response = make_response(
        200,
        {
            "state_id": 1,
            "camera_id": 1,
            "mode": "Active",
            "fps": 5,
            "resolution": "720p",
        },
    )
    updated_camera = {
        "state_id": 1,
        "camera_id": 1,
        "mode": "Dormant",
        "fps": 5,
        "resolution": "720p",
        "timestamp": "2026-09-21T20:05:00Z",
    }
    update_response = make_response(200, updated_camera)
    state = {
        "camera_id": 1,
        "mode": "Dormant",
        "fps": 5,
        "resolution": "720p",
    }

    client._request = Mock(
        side_effect=[
            lookup_response,
            update_response,
        ]
    )

    result = client.set_camera_state(state)

    assert result == updated_camera
    assert client._request.call_args_list == [
        call(
            "GET",
            "/camera-states/1",
        ),
        call(
            "PUT",
            "/camera-states/1",
            json_body={
                "mode": "Dormant",
                "fps": 5,
                "resolution": "720p",
            },
        ),
    ]


def test_set_camera_state_rejects_unexpected_lookup_error():
    client = HeimdallVisionClient()

    lookup_response = make_response(
        500,
        {"detail": "Internal server error."},
    )
    client._request = Mock(return_value=lookup_response)

    with pytest.raises(
        HeimdallAPIError,
        match="500",
    ):
        client.set_camera_state(
            {
                "camera_id": 1,
                "mode": "Active",
                "fps": 5,
                "resolution": "720p",
            }
        )


def test_authenticate_adds_bearer_token():
    client = HeimdallVisionClient(
        username="vision.operator",
        password="SecureVisionPassword123!",
    )
    response = make_response(
        200,
        {
            "access_token": "signed-token",
            "token_type": "bearer",
        },
    )
    client._request = Mock(return_value=response)

    client.authenticate()

    client._request.assert_called_once_with(
        "POST",
        "/auth/login",
        json_body={
            "username": "vision.operator",
            "password": "SecureVisionPassword123!",
        },
    )
    assert client._session.headers["Authorization"] == "Bearer signed-token"


def test_authenticate_requires_credentials(monkeypatch):
    monkeypatch.delenv("VISION_API_USERNAME", raising=False)
    monkeypatch.delenv("VISION_API_PASSWORD", raising=False)

    client = HeimdallVisionClient()

    with pytest.raises(
        HeimdallAPIError,
        match="credentials are missing",
    ):
        client.authenticate()


def test_authenticate_requires_access_token():
    client = HeimdallVisionClient(
        username="vision.operator",
        password="SecureVisionPassword123!",
    )
    response = make_response(
        200,
        {"token_type": "bearer"},
    )
    client._request = Mock(return_value=response)

    with pytest.raises(
        HeimdallAPIError,
        match="did not include an access token",
    ):
        client.authenticate()
