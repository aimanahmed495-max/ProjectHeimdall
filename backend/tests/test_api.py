import pytest


def create_threat(client):
    response = client.post(
        "/threat-events",
        json={
            "object_class": "Firearm",
            "confidence_score": 0.92,
            "camera_id": 1,
            "status": "Pending",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health_check_confirms_database_connection(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "connected",
    }


def test_create_and_get_osint_source(client):
    create_response = client.post(
        "/sources",
        json={
            "source_name": "National Weather Service",
            "source_type": "Public API",
            "url": "https://www.weather.gov/",
            "reliability_score": 0.95,
        },
    )

    assert create_response.status_code == 201

    source = create_response.json()
    assert source["source_id"] > 0
    assert source["source_name"] == "National Weather Service"
    assert source["reliability_score"] == 0.95

    get_response = client.get("/sources")

    assert get_response.status_code == 200
    assert len(get_response.json()) == 1


def test_duplicate_source_name_returns_conflict(client):
    source_data = {
        "source_name": "Emergency Feed",
        "source_type": "Emergency Broadcast",
        "url": "https://example.com/emergency",
        "reliability_score": 0.9,
    }

    first_response = client.post("/sources", json=source_data)
    second_response = client.post("/sources", json=source_data)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_source_reliability_must_be_between_zero_and_one(client, score):
    response = client.post(
        "/sources",
        json={
            "source_name": "Invalid Source",
            "source_type": "RSS Feed",
            "url": "https://example.com/feed",
            "reliability_score": score,
        },
    )

    assert response.status_code == 422


def test_create_and_get_threat_event(client):
    threat = create_threat(client)

    assert threat["event_id"] > 0
    assert threat["object_class"] == "Firearm"
    assert threat["confidence_score"] == 0.92
    assert threat["camera_id"] == 1
    assert threat["status"] == "Pending"
    assert "timestamp" in threat

    get_response = client.get("/threat-events")

    assert get_response.status_code == 200
    assert len(get_response.json()) == 1


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_threat_confidence_must_be_between_zero_and_one(client, score):
    response = client.post(
        "/threat-events",
        json={
            "object_class": "Edged Weapon",
            "confidence_score": score,
            "camera_id": 1,
            "status": "Pending",
        },
    )

    assert response.status_code == 422


def test_threat_event_requires_positive_camera_id(client):
    response = client.post(
        "/threat-events",
        json={
            "object_class": "Firearm",
            "confidence_score": 0.8,
            "camera_id": 0,
            "status": "Pending",
        },
    )

    assert response.status_code == 422


def test_create_and_get_alert_log(client):
    threat = create_threat(client)

    create_response = client.post(
        "/alert-logs",
        json={
            "event_id": threat["event_id"],
            "alert_level": "Critical",
            "message": "High-confidence firearm detection",
            "acknowledged": False,
        },
    )

    assert create_response.status_code == 201

    alert = create_response.json()
    assert alert["alert_id"] > 0
    assert alert["event_id"] == threat["event_id"]
    assert alert["alert_level"] == "Critical"
    assert alert["acknowledged"] is False
    assert "alert_time" in alert

    get_response = client.get("/alert-logs")

    assert get_response.status_code == 200
    assert len(get_response.json()) == 1


def test_alert_log_requires_existing_threat(client):
    response = client.post(
        "/alert-logs",
        json={
            "event_id": 2147483647,
            "alert_level": "High",
            "message": "Unknown threat",
            "acknowledged": False,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Threat event not found."


def test_create_and_get_camera_state(client):
    create_response = client.post(
        "/camera-states",
        json={
            "camera_id": 1,
            "mode": "Dormant",
            "fps": 5,
            "resolution": "720p",
        },
    )

    assert create_response.status_code == 201

    camera_state = create_response.json()
    assert camera_state["state_id"] > 0
    assert camera_state["camera_id"] == 1
    assert camera_state["mode"] == "Dormant"
    assert camera_state["fps"] == 5
    assert "timestamp" in camera_state

    get_response = client.get("/camera-states")

    assert get_response.status_code == 200
    assert len(get_response.json()) == 1


@pytest.mark.parametrize("mode", ["Sleeping", "High Alert"])
def test_camera_state_rejects_unknown_mode(client, mode):
    response = client.post(
        "/camera-states",
        json={
            "camera_id": 1,
            "mode": mode,
            "fps": 5,
            "resolution": "720p",
        },
    )

    assert response.status_code == 422


def test_camera_state_requires_positive_fps(client):
    response = client.post(
        "/camera-states",
        json={
            "camera_id": 1,
            "mode": "Active",
            "fps": 0,
            "resolution": "1080p",
        },
    )

    assert response.status_code == 422


def test_create_system_log_without_threat_event(client):
    create_response = client.post(
        "/system-logs",
        json={
            "event_id": None,
            "module": "OSINT",
            "message": "OSINT polling started",
        },
    )

    assert create_response.status_code == 201

    system_log = create_response.json()
    assert system_log["log_id"] > 0
    assert system_log["event_id"] is None
    assert system_log["module"] == "OSINT"

    get_response = client.get("/system-logs")

    assert get_response.status_code == 200
    assert len(get_response.json()) == 1


def test_create_system_log_with_threat_event(client):
    threat = create_threat(client)

    response = client.post(
        "/system-logs",
        json={
            "event_id": threat["event_id"],
            "module": "Core API",
            "message": "Threat event stored",
        },
    )

    assert response.status_code == 201
    assert response.json()["event_id"] == threat["event_id"]


def test_system_log_rejects_missing_threat_event(client):
    response = client.post(
        "/system-logs",
        json={
            "event_id": 2147483647,
            "module": "Core API",
            "message": "Unknown event",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Threat event not found."