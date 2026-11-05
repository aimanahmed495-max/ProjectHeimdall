"""OSINT pipeline E2E: two sources agree, and the real API records it.

The live runner, keyword filter, tracker, activator, and HTTP client are the
production classes. Only the sources and the classifier are fakes, so there is
no Groq call and no network traffic beyond the local API.
"""

from datetime import datetime, timedelta, timezone

import pytest
from camera_activation import CameraActivator
from corroboration import CorroborationTracker
from keyword_filter import KeywordFilter
from live_osint import LiveOsintRunner
from source_adapter import SourceAdapter, SourceItem

pytestmark = pytest.mark.e2e

SHARED_CLASS = "person"
ALPHA = "e2e-alpha-source"
BETA = "e2e-beta-source"


class StaticAdapter(SourceAdapter):
    """Yields preloaded batches, one batch per poll."""

    def __init__(self, source_name, batches):
        super().__init__(source_name)
        self._batches = list(batches)

    def registration_payload(self):
        return {
            "source_name": self.source_name,
            "source_type": "Test",
            "url": "https://example.com/test",
            "reliability_score": 0.5,
        }

    def _fetch_items(self):
        if not self._batches:
            return []
        return self._batches.pop(0)


class ScriptedClassifier:
    """Stands in for ``OsintAgent``: fixed class, real ``POST /threat-events``."""

    def __init__(self, client, object_class):
        self._client = client
        self._object_class = object_class
        self.event_ids = []

    def run(self, alert_text, source_id):
        threat_event = self._client.post_threat_event(
            {
                "source_id": source_id,
                "object_class": self._object_class,
                "confidence_score": 0.9,
                "status": "Pending",
            }
        )
        self.event_ids.append(threat_event["event_id"])
        return {
            "alert_text": alert_text,
            "source_id": source_id,
            "object_class": self._object_class,
            "confidence_score": 0.9,
            "threat_event": threat_event,
            "error": None,
        }


def single_batch(source_name, text, external_id, timestamp):
    """Build an adapter that yields one item on its first poll."""

    item = SourceItem(source_name, text, timestamp, external_id)
    return StaticAdapter(source_name, [[item]])


def test_matching_sources_activate_camera_and_corroborate_events(
    api, osint_client, dormant_camera
):
    """Same class from two sources: camera 1 goes Active, both events Corroborated."""

    now = datetime.now(timezone.utc)
    adapters = [
        single_batch(ALPHA, "gun seen near the north gate", "alpha-1", now),
        single_batch(
            BETA,
            "man with a gun at the north gate",
            "beta-1",
            now + timedelta(seconds=10),
        ),
    ]
    classifier = ScriptedClassifier(osint_client, SHARED_CLASS)
    runner = LiveOsintRunner(
        client=osint_client,
        agent=classifier,
        adapters=adapters,
        keyword_filter=KeywordFilter(["gun"]),
        tracker=CorroborationTracker(window_seconds=300),
        activator=CameraActivator(osint_client, camera_id=dormant_camera),
        poll_interval=1,
        sleep=lambda _delay: None,
    )

    assert runner.run(max_cycles=1) == 0

    camera = api.get(f"/camera-states/{dormant_camera}")
    assert camera.status_code == 200, camera.text
    assert camera.json()["mode"] == "Active"

    assert len(classifier.event_ids) == 2
    events = [
        api.get(f"/threat-events/{event_id}") for event_id in classifier.event_ids
    ]
    for event in events:
        assert event.status_code == 200, event.text
        body = event.json()
        assert body["status"] == "Corroborated"
        assert body["corroborated_at"] is not None
        assert body["object_class"] == SHARED_CLASS
    source_ids = {event.json()["source_id"] for event in events}
    assert len(source_ids) == 2
