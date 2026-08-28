def create_source(client, name="Test OSINT Source", is_active=True):
    response = client.post(
        "/sources",
        json={
            "name": name,
            "source_type": "OSINT",
            "is_active": is_active,
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


def test_create_and_get_source(client):
    created_source = create_source(client)

    response = client.get("/sources")

    assert response.status_code == 200
    assert response.json() == [created_source]


def test_duplicate_source_name_returns_conflict(client):
    create_source(client)

    response = client.post(
        "/sources",
        json={
            "name": "Test OSINT Source",
            "source_type": "OSINT",
            "is_active": True,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "A source with this name already exists."


def test_create_and_get_threat_event(client):
    source = create_source(client)

    response = client.post(
        "/threat-events",
        json={
            "source_id": source["id"],
            "threat_score": 82,
            "summary": "Mock suspicious activity",
            "metadata": {
                "location": "Wichita",
                "mock": True,
            },
        },
    )

    assert response.status_code == 201

    created_event = response.json()
    assert created_event["threat_level"] == "HIGH_THREAT"
    assert created_event["source_id"] == source["id"]
    assert created_event["metadata"]["location"] == "Wichita"

    get_response = client.get("/threat-events")

    assert get_response.status_code == 200
    assert get_response.json() == [created_event]


def test_invalid_threat_score_returns_validation_error(client):
    source = create_source(client)

    response = client.post(
        "/threat-events",
        json={
            "source_id": source["id"],
            "threat_score": 101,
            "summary": "Invalid score",
            "metadata": {},
        },
    )

    assert response.status_code == 422


def test_missing_source_returns_not_found(client):
    response = client.post(
        "/threat-events",
        json={
            "source_id": 2147483647,
            "threat_score": 82,
            "summary": "Unknown source",
            "metadata": {},
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "OSINT source not found."


def test_inactive_source_cannot_create_threat(client):
    source = create_source(client, is_active=False)

    response = client.post(
        "/threat-events",
        json={
            "source_id": source["id"],
            "threat_score": 82,
            "summary": "Inactive source event",
            "metadata": {},
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "OSINT source is inactive."


def test_threat_events_are_ordered_by_highest_score(client):
    source = create_source(client)

    for score in [25, 95, 60]:
        response = client.post(
            "/threat-events",
            json={
                "source_id": source["id"],
                "threat_score": score,
                "summary": f"Threat score {score}",
                "metadata": {},
            },
        )
        assert response.status_code == 201

    response = client.get("/threat-events")

    assert response.status_code == 200
    scores = [event["threat_score"] for event in response.json()]
    assert scores == [95, 60, 25]