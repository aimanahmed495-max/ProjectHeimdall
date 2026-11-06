"""OSINT pipeline E2E: matching sources, negatives, and failure isolation.

The live runner, keyword filter, tracker, activator, and HTTP client are the
production classes. Only the sources and the classifier are fakes, so there is
no Groq call and no network traffic beyond the local API.
"""

from datetime import datetime, timedelta, timezone

import pytest
import requests
from camera_activation import CameraActivator
from corroboration import CorroborationTracker
from keyword_filter import KeywordFilter
from live_osint import LiveOsintRunner
from source_adapter import SourceAdapter, SourceItem

pytestmark = pytest.mark.e2e

SHARED_CLASS = "person"
OTHER_CLASS = "vehicle"
ALPHA = "e2e-alpha-source"
BETA = "e2e-beta-source"
WINDOW_SECONDS = 300


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


class FailingAdapter(StaticAdapter):
    """Raises a request error on every poll."""

    def _fetch_items(self):
        raise requests.ConnectionError("feed unreachable")


class ScriptedClassifier:
    """Stands in for ``OsintAgent``: fixed or queued classes, real threat posts."""

    def __init__(self, client, object_classes):
        """Post each call with the next class from ``object_classes``.

        Args:
            client: Authenticated Heimdall API client.
            object_classes: One class string, or a sequence consumed per call.
        """

        if isinstance(object_classes, str):
            self._classes = iter([object_classes] * 32)
        else:
            self._classes = iter(object_classes)
        self._client = client
        self.event_ids = []
        self.calls = []

    def run(self, alert_text, source_id):
        object_class = next(self._classes)
        threat_event = self._client.post_threat_event(
            {
                "source_id": source_id,
                "object_class": object_class,
                "confidence_score": 0.9,
                "status": "Pending",
            }
        )
        self.event_ids.append(threat_event["event_id"])
        self.calls.append((alert_text, source_id, object_class))
        return {
            "alert_text": alert_text,
            "source_id": source_id,
            "object_class": object_class,
            "confidence_score": 0.9,
            "threat_event": threat_event,
            "error": None,
        }


def single_batch(source_name, text, external_id, timestamp):
    """Build an adapter that yields one item on its first poll."""

    item = SourceItem(source_name, text, timestamp, external_id)
    return StaticAdapter(source_name, [[item]])


def build_runner(
    client, adapters, classifier, window_seconds=WINDOW_SECONDS, camera_id=1
):
    """Wire production loop pieces around the given fakes."""

    return LiveOsintRunner(
        client=client,
        agent=classifier,
        adapters=adapters,
        keyword_filter=KeywordFilter(["gun"]),
        tracker=CorroborationTracker(window_seconds=window_seconds),
        activator=CameraActivator(client, camera_id=camera_id),
        poll_interval=1,
        sleep=lambda _delay: None,
    )


def assert_camera_mode(api, camera_id, mode):
    """Fetch camera ``camera_id`` and require ``mode``."""

    camera = api.get(f"/camera-states/{camera_id}")
    assert camera.status_code == 200, camera.text
    assert camera.json()["mode"] == mode


def assert_events_status(api, event_ids, status):
    """Require every threat event to have ``status``."""

    for event_id in event_ids:
        event = api.get(f"/threat-events/{event_id}")
        assert event.status_code == 200, event.text
        body = event.json()
        assert body["status"] == status
        if status != "Corroborated":
            assert body["corroborated_at"] is None


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
    runner = build_runner(
        osint_client, adapters, classifier, camera_id=dormant_camera
    )

    assert runner.run(max_cycles=1) == 0

    assert_camera_mode(api, dormant_camera, "Active")
    assert len(classifier.event_ids) == 2
    assert_events_status(api, classifier.event_ids, "Corroborated")
    events = [
        api.get(f"/threat-events/{event_id}") for event_id in classifier.event_ids
    ]
    for event in events:
        assert event.json()["object_class"] == SHARED_CLASS
    source_ids = {event.json()["source_id"] for event in events}
    assert len(source_ids) == 2


def test_different_classes_leave_camera_dormant(api, osint_client, dormant_camera):
    """Two sources reporting different classes do not activate the camera."""

    now = datetime.now(timezone.utc)
    adapters = [
        single_batch(ALPHA, "gun seen near the north gate", "alpha-diff-1", now),
        single_batch(
            BETA,
            "gun seen near a parked truck",
            "beta-diff-1",
            now + timedelta(seconds=10),
        ),
    ]
    classifier = ScriptedClassifier(osint_client, [SHARED_CLASS, OTHER_CLASS])
    runner = build_runner(
        osint_client, adapters, classifier, camera_id=dormant_camera
    )

    assert runner.run(max_cycles=1) == 0

    assert_camera_mode(api, dormant_camera, "Dormant")
    assert len(classifier.event_ids) == 2
    assert_events_status(api, classifier.event_ids, "Pending")
    classes = {call[2] for call in classifier.calls}
    assert classes == {SHARED_CLASS, OTHER_CLASS}


def test_reports_outside_the_window_do_not_corroborate(
    api, osint_client, dormant_camera
):
    """A second source outside the window leaves the camera Dormant."""

    now = datetime.now(timezone.utc)
    adapters = [
        single_batch(ALPHA, "gun seen near the north gate", "alpha-window-1", now),
        single_batch(
            BETA,
            "man with a gun at the north gate",
            "beta-window-1",
            now + timedelta(seconds=WINDOW_SECONDS + 1),
        ),
    ]
    classifier = ScriptedClassifier(osint_client, SHARED_CLASS)
    runner = build_runner(
        osint_client, adapters, classifier, camera_id=dormant_camera
    )

    assert runner.run(max_cycles=1) == 0

    assert_camera_mode(api, dormant_camera, "Dormant")
    assert len(classifier.event_ids) == 2
    assert_events_status(api, classifier.event_ids, "Pending")


def test_one_source_request_error_does_not_stop_the_runner(
    api, osint_client, dormant_camera
):
    """A failing source is skipped; the healthy source still classifies."""

    now = datetime.now(timezone.utc)
    adapters = [
        FailingAdapter(ALPHA, []),
        single_batch(
            BETA,
            "man with a gun at the north gate",
            "beta-error-1",
            now,
        ),
    ]
    classifier = ScriptedClassifier(osint_client, SHARED_CLASS)
    runner = build_runner(
        osint_client, adapters, classifier, camera_id=dormant_camera
    )

    assert runner.run(max_cycles=1) == 0

    assert_camera_mode(api, dormant_camera, "Dormant")
    assert len(classifier.event_ids) == 1
    assert_events_status(api, classifier.event_ids, "Pending")
    assert classifier.calls[0][1] is not None


def test_same_source_twice_does_not_corroborate(api, osint_client, dormant_camera):
    """Two reports from one source never activate the camera."""

    now = datetime.now(timezone.utc)
    items = [
        SourceItem(ALPHA, "gun seen near the north gate", now, "alpha-same-1"),
        SourceItem(
            ALPHA,
            "gun seen again near the north gate",
            now + timedelta(seconds=10),
            "alpha-same-2",
        ),
    ]
    adapters = [StaticAdapter(ALPHA, [items])]
    classifier = ScriptedClassifier(osint_client, SHARED_CLASS)
    runner = build_runner(
        osint_client, adapters, classifier, camera_id=dormant_camera
    )

    assert runner.run(max_cycles=1) == 0

    assert_camera_mode(api, dormant_camera, "Dormant")
    assert len(classifier.event_ids) == 2
    assert_events_status(api, classifier.event_ids, "Pending")
    source_ids = {
        api.get(f"/threat-events/{event_id}").json()["source_id"]
        for event_id in classifier.event_ids
    }
    assert len(source_ids) == 1
