from fastapi.testclient import TestClient

from frontend.demo_backend.main import alerts, app


client = TestClient(app)


def setup_function() -> None:
    alerts.clear()


def test_health_endpoint() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_acknowledge_alert() -> None:
    created = client.post(
        "/api/demo/alerts",
        json={
            "title": "Test threat",
            "location": "Test location",
            "confidence": 90,
        },
    )

    assert created.status_code == 201
    alert = created.json()
    assert alert["status"] == "active"
    assert alert["severity"] == "high"

    acknowledged = client.patch(
        f"/api/alerts/{alert['id']}/acknowledge"
    )

    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"


def test_websocket_receives_new_alert() -> None:
    with client.websocket_connect("/ws/events") as websocket:
        ready = websocket.receive_json()
        assert ready["type"] == "connection.ready"

        created = client.post(
            "/api/demo/alerts",
            json={"confidence": 82},
        )
        assert created.status_code == 201

        event = websocket.receive_json()
        assert event["type"] == "alert.created"
        assert event["data"]["confidence"] == 82
