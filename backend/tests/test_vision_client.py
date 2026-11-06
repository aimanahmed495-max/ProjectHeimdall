from unittest.mock import Mock, call

import pytest

from vision.vision_client import HeimdallAPIError, HeimdallVisionClient


def make_response(status_code, payload, method="GET", url="http://localhost:8000/x"):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    response.text = str(payload)
    response.request.method = method
    response.url = url
    return response


def test_get_camera_state_returns_payload_on_200():
    client = HeimdallVisionClient()
    payload = {
        "state_id": 1,
        "camera_id": 1,
        "mode": "Active",
        "fps": 5,
        "resolution": "720p",
    }
    client._send = Mock(return_value=make_response(200, payload))

    result = client.get_camera_state(1)

    assert result == payload
    client._send.assert_called_once_with("GET", "/camera-states/1", json_body=None)


def test_get_camera_state_returns_none_on_404():
    client = HeimdallVisionClient()
    client._send = Mock(
        return_value=make_response(404, {"detail": "Camera state not found."})
    )

    assert client.get_camera_state(99) is None


def test_get_camera_state_rejects_unexpected_status():
    client = HeimdallVisionClient()
    client._send = Mock(
        return_value=make_response(500, {"detail": "Internal server error."})
    )

    with pytest.raises(HeimdallAPIError, match="500"):
        client.get_camera_state(1)


def test_request_reauthenticates_once_on_401():
    client = HeimdallVisionClient(
        username="vision.operator",
        password="SecureVisionPassword123!",
    )
    unauthorized = make_response(401, {"detail": "expired"})
    ok = make_response(
        200,
        {
            "state_id": 1,
            "camera_id": 1,
            "mode": "Dormant",
            "fps": 5,
            "resolution": "720p",
        },
    )
    login = make_response(
        200,
        {"access_token": "fresh-token", "token_type": "bearer"},
        method="POST",
        url="http://localhost:8000/auth/login",
    )
    client._send = Mock(side_effect=[unauthorized, login, ok])

    result = client.get_camera_state(1)

    assert result["mode"] == "Dormant"
    assert client._session.headers["Authorization"] == "Bearer fresh-token"
    assert client._send.call_args_list == [
        call("GET", "/camera-states/1", json_body=None),
        call(
            "POST",
            "/auth/login",
            json_body={
                "username": "vision.operator",
                "password": "SecureVisionPassword123!",
            },
        ),
        call("GET", "/camera-states/1", json_body=None),
    ]


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
    client._send = Mock(return_value=response)

    client.authenticate()

    client._send.assert_called_once_with(
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
    client._send = Mock(return_value=response)

    with pytest.raises(
        HeimdallAPIError,
        match="did not include an access token",
    ):
        client.authenticate()
