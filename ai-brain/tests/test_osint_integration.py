from unittest.mock import Mock

import pytest
from main import OsintIngestionApp
from osint_agent import OsintAgent
from osint_client import HeimdallAPIClient, HeimdallAPIError


def make_response(status_code, payload):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    response.text = str(payload)
    response.request.method = "POST"
    response.url = "http://localhost:8000/auth/login"
    return response


def test_authenticate_adds_bearer_token():
    client = HeimdallAPIClient(
        username="osint.service",
        password="SecureOsintPassword123!",
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
            "username": "osint.service",
            "password": "SecureOsintPassword123!",
        },
    )
    assert client._session.headers["Authorization"] == "Bearer signed-token"


def test_authenticate_requires_credentials(monkeypatch):
    monkeypatch.delenv("OSINT_API_USERNAME", raising=False)
    monkeypatch.delenv("OSINT_API_PASSWORD", raising=False)

    client = HeimdallAPIClient()

    with pytest.raises(HeimdallAPIError, match="credentials are missing"):
        client.authenticate()


def test_alerts_are_mapped_to_registered_source_ids():
    app = object.__new__(OsintIngestionApp)

    alerts = [
        {
            "source_name": "Local News Crime Desk",
            "alert_text": "Reported break-in",
        }
    ]
    sources = [
        {
            "source_id": 12,
            "source_name": "Local News Crime Desk",
        }
    ]

    result = app._attach_source_ids(alerts, sources)

    assert result == [
        {
            "source_name": "Local News Crime Desk",
            "alert_text": "Reported break-in",
            "source_id": 12,
        }
    ]


def test_unknown_alert_source_is_rejected():
    app = object.__new__(OsintIngestionApp)

    with pytest.raises(ValueError, match="unregistered source"):
        app._attach_source_ids(
            [
                {
                    "source_name": "Unknown Source",
                    "alert_text": "Test report",
                }
            ],
            [],
        )


def test_osint_event_uses_source_without_fake_camera():
    agent = object.__new__(OsintAgent)
    agent._client = Mock()
    agent._client.post_threat_event.return_value = {
        "event_id": 99,
        "source_id": 12,
        "camera_id": None,
    }
    agent._client.post_system_log.return_value = {"log_id": 20}

    result = agent._post_to_api(
        {
            "source_id": 12,
            "alert_text": "Vehicle circling the parking lot",
            "object_class": "vehicle",
            "confidence_score": 0.9,
        }
    )

    agent._client.post_threat_event.assert_called_once_with(
        {
            "source_id": 12,
            "object_class": "vehicle",
            "confidence_score": 0.9,
            "status": "Pending",
        }
    )
    assert "camera_id" not in (
        agent._client.post_threat_event.call_args.kwargs
        or agent._client.post_threat_event.call_args.args[0]
    )
    assert result["threat_event"]["camera_id"] is None
