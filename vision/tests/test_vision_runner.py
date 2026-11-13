"""Unit tests for VisionRunner. No network, model, or camera."""

from __future__ import annotations

import logging

import pytest
from fakes import (
    FakeClient,
    FakeDetector,
    FakeFrame,
    FakeFrameSource,
    FakePreview,
    HeimdallAPIUnavailableError,
    make_settings,
)

from frame_sources import PI_CAMERA_MESSAGE
from throttle import DetectionThrottle
from vision_runner import VisionRunner


def advancing_clock(start: float = 0.0):
    """Return ``(clock, sleep)`` that advances time when sleep is called."""

    now = [start]

    def clock() -> float:
        return now[0]

    def sleep(delay: float) -> None:
        now[0] += delay

    return clock, sleep


def active_state(fps: float = 5) -> dict:
    return {
        "camera_id": 1,
        "mode": "Active",
        "fps": fps,
        "resolution": "720p",
    }


def dormant_state() -> dict:
    return {
        "camera_id": 1,
        "mode": "Dormant",
        "fps": 5,
        "resolution": "720p",
    }


def test_dormant_camera_does_not_open_or_post():
    client = FakeClient([dormant_state()])
    source = FakeFrameSource()
    detector = FakeDetector()
    clock, sleep = advancing_clock()
    runner = VisionRunner(
        client,
        detector,
        source,
        make_settings(state_poll_seconds=1.0),
        sleep=sleep,
        clock=clock,
    )

    assert runner.run(max_cycles=1) == 0

    assert source.open_count == 0
    assert detector.calls == 0
    assert client.threat_events == []
    assert client.system_logs == []


def test_dormant_then_active_opens_and_posts():
    client = FakeClient([dormant_state(), active_state(fps=2)])
    source = FakeFrameSource()
    detector = FakeDetector([("person", 0.91)])
    clock, sleep = advancing_clock()
    runner = VisionRunner(
        client,
        detector,
        source,
        make_settings(
            camera_id=7,
            state_poll_seconds=1.0,
            event_cooldown_seconds=0.0,
        ),
        sleep=sleep,
        clock=clock,
    )

    assert runner.run(max_cycles=2) == 0

    assert source.open_count >= 1
    assert detector.calls >= 1
    assert len(client.threat_events) >= 1
    event = client.threat_events[0]
    assert event["camera_id"] == 7
    assert event["status"] == "Pending"
    assert event["object_class"] == "person"
    assert client.system_logs[0]["module"] == "vision"


def test_active_then_dormant_closes_source():
    client = FakeClient([active_state(fps=2), dormant_state()])
    source = FakeFrameSource()
    detector = FakeDetector()
    clock, sleep = advancing_clock()
    settings = make_settings(state_poll_seconds=1.0, event_cooldown_seconds=0.0)
    runner = VisionRunner(
        client,
        detector,
        source,
        settings,
        sleep=sleep,
        clock=clock,
    )

    assert runner.run(max_cycles=1) == 0
    posts_after_active = len(client.threat_events)
    assert source.open_count >= 1
    assert posts_after_active >= 1

    assert runner.run(max_cycles=1) == 0
    assert source.is_open is False
    assert source.close_count >= 1
    assert len(client.threat_events) == posts_after_active
    assert detector.calls == posts_after_active


def test_camera_404_logs_warning_and_keeps_polling(caplog):
    client = FakeClient([None, None])
    source = FakeFrameSource()
    clock, sleep = advancing_clock()
    runner = VisionRunner(
        client,
        FakeDetector(),
        source,
        make_settings(state_poll_seconds=1.0),
        sleep=sleep,
        clock=clock,
    )

    with caplog.at_level(logging.WARNING):
        assert runner.run(max_cycles=2) == 0

    assert source.open_count == 0
    assert client.threat_events == []
    assert any("not found" in record.message.lower() for record in caplog.records)


def test_runner_never_writes_camera_state():
    client = FakeClient([active_state(fps=2)])
    clock, sleep = advancing_clock()
    runner = VisionRunner(
        client,
        FakeDetector(),
        FakeFrameSource(),
        make_settings(state_poll_seconds=1.0, event_cooldown_seconds=0.0),
        sleep=sleep,
        clock=clock,
    )

    assert runner.run(max_cycles=1) == 0
    # FakeClient raises AssertionError if post/set_camera_state are called.
    assert not hasattr(client, "set_camera_state_called")


def test_frame_pacing_follows_row_fps():
    client = FakeClient([active_state(fps=5)])
    source = FakeFrameSource()
    detector = FakeDetector()
    sleeps: list[float] = []
    now = [0.0]

    def clock() -> float:
        return now[0]

    def sleep(delay: float) -> None:
        sleeps.append(delay)
        now[0] += delay

    runner = VisionRunner(
        client,
        detector,
        source,
        make_settings(state_poll_seconds=1.0, event_cooldown_seconds=0.0),
        sleep=sleep,
        clock=clock,
    )

    assert runner.run(max_cycles=1) == 0

    assert sleeps
    assert all(pytest.approx(delay, rel=1e-6) == 0.2 for delay in sleeps)
    assert detector.calls == len(sleeps) == 5


def test_api_unavailable_keeps_polling_and_releases_source(caplog):
    client = FakeClient()
    source = FakeFrameSource()
    clock, sleep = advancing_clock()
    calls = {"n": 0}

    def flaky_get(camera_id: int):
        calls["n"] += 1
        if calls["n"] == 1:
            return active_state(fps=2)
        raise HeimdallAPIUnavailableError("down")

    client.get_camera_state = flaky_get  # type: ignore[method-assign]
    runner = VisionRunner(
        client,
        FakeDetector(),
        source,
        make_settings(state_poll_seconds=1.0, event_cooldown_seconds=0.0),
        sleep=sleep,
        clock=clock,
    )

    assert runner.run(max_cycles=1) == 0
    assert source.open_count >= 1

    with caplog.at_level(logging.WARNING):
        assert runner.run(max_cycles=1) == 0

    assert source.is_open is False
    assert any("unavailable" in record.message.lower() for record in caplog.records)


def test_keyboard_interrupt_closes_source_and_returns_zero():
    client = FakeClient()
    source = FakeFrameSource()
    clock, sleep = advancing_clock()

    def boom(_camera_id: int):
        raise KeyboardInterrupt()

    client.get_camera_state = boom  # type: ignore[method-assign]
    runner = VisionRunner(
        client,
        FakeDetector(),
        source,
        make_settings(),
        sleep=sleep,
        clock=clock,
    )
    source.open()

    assert runner.run(max_cycles=1) == 0
    assert source.is_open is False
    assert source.close_count >= 1


def test_pi_source_failure_exits_one():
    client = FakeClient([active_state(fps=2)])
    source = FakeFrameSource(fail_open=RuntimeError(PI_CAMERA_MESSAGE))
    clock, sleep = advancing_clock()
    runner = VisionRunner(
        client,
        FakeDetector(),
        source,
        make_settings(state_poll_seconds=1.0),
        sleep=sleep,
        clock=clock,
    )

    assert runner.run(max_cycles=1) == 1
    assert source.is_open is False


def test_throttle_posts_once_inside_cooldown_then_again():
    clock, _sleep = advancing_clock()
    throttle = DetectionThrottle(cooldown_seconds=10.0, clock=clock)

    assert throttle.allow("person") is True
    assert throttle.allow("person") is False
    assert throttle.allow("car") is True
    _sleep(10.0)
    assert throttle.allow("person") is True


def test_runner_applies_throttle_across_frames():
    client = FakeClient([active_state(fps=5)])
    source = FakeFrameSource()
    detector = FakeDetector([("person", 0.9), ("car", 0.8)])
    clock, sleep = advancing_clock()
    runner = VisionRunner(
        client,
        detector,
        source,
        make_settings(state_poll_seconds=1.0, event_cooldown_seconds=30.0),
        sleep=sleep,
        clock=clock,
        throttle=DetectionThrottle(30.0, clock=clock),
    )

    assert runner.run(max_cycles=1) == 0

    classes = [event["object_class"] for event in client.threat_events]
    assert classes.count("person") == 1
    assert classes.count("car") == 1


def test_active_frames_update_fake_preview():
    frame = FakeFrame("cam")
    client = FakeClient([active_state(fps=2)])
    source = FakeFrameSource(frames=[("frame-1", frame)])
    detector = FakeDetector([("person", 0.88)])
    preview = FakePreview()
    clock, sleep = advancing_clock()
    runner = VisionRunner(
        client,
        detector,
        source,
        make_settings(state_poll_seconds=1.0, event_cooldown_seconds=0.0),
        sleep=sleep,
        clock=clock,
        preview=preview,
    )

    assert runner.run(max_cycles=1) == 0

    assert preview.shown
    shown_frame, shown_detections = preview.shown[0]
    assert shown_frame is frame
    assert shown_detections == [("person", 0.88)]
    assert preview.close_count >= 1


def test_dormant_closes_preview_without_show():
    client = FakeClient([dormant_state()])
    preview = FakePreview()
    clock, sleep = advancing_clock()
    runner = VisionRunner(
        client,
        FakeDetector(),
        FakeFrameSource(),
        make_settings(state_poll_seconds=1.0),
        sleep=sleep,
        clock=clock,
        preview=preview,
    )

    assert runner.run(max_cycles=1) == 0

    assert preview.shown == []
    assert preview.close_count >= 1
