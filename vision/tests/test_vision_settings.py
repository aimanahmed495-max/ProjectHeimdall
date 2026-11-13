"""Unit tests for vision environment settings."""

from __future__ import annotations

import logging

import vision_settings as settings


def test_pi_camera_flag_accepted_spellings(monkeypatch):
    for raw in ("1", "true", "YES", "On"):
        monkeypatch.setenv("FEATURE_PI_CAMERA", raw)
        assert settings.pi_camera_enabled() is True


def test_pi_camera_flag_defaults_and_unknown(monkeypatch):
    monkeypatch.delenv("FEATURE_PI_CAMERA", raising=False)
    assert settings.pi_camera_enabled() is False
    monkeypatch.setenv("FEATURE_PI_CAMERA", "maybe")
    assert settings.pi_camera_enabled() is False


def test_show_window_flag_accepted_spellings(monkeypatch):
    for raw in ("1", "true", "YES", "On"):
        monkeypatch.setenv("VISION_SHOW_WINDOW", raw)
        assert settings.show_window_enabled() is True


def test_show_window_flag_defaults_and_unknown(monkeypatch):
    monkeypatch.delenv("VISION_SHOW_WINDOW", raising=False)
    assert settings.show_window_enabled() is False
    monkeypatch.setenv("VISION_SHOW_WINDOW", "maybe")
    assert settings.show_window_enabled() is False


def test_numeric_defaults_and_invalid_fallback(monkeypatch, caplog):
    monkeypatch.delenv("VISION_CAMERA_ID", raising=False)
    monkeypatch.delenv("VISION_STATE_POLL_SECONDS", raising=False)
    monkeypatch.delenv("VISION_EVENT_COOLDOWN_SECONDS", raising=False)
    monkeypatch.delenv("VISION_FRAME_SOURCE", raising=False)

    assert settings.camera_id() == 1
    assert settings.state_poll_seconds() == 2.0
    assert settings.event_cooldown_seconds() == 30.0
    assert settings.frame_source() == "0"

    monkeypatch.setenv("VISION_CAMERA_ID", "nope")
    monkeypatch.setenv("VISION_STATE_POLL_SECONDS", "-1")
    monkeypatch.setenv("VISION_EVENT_COOLDOWN_SECONDS", "abc")
    with caplog.at_level(logging.WARNING):
        assert settings.camera_id() == 1
        assert settings.state_poll_seconds() == 2.0
        assert settings.event_cooldown_seconds() == 30.0
    assert len(caplog.records) >= 3


def test_load_settings_reads_env(monkeypatch):
    monkeypatch.setenv("FEATURE_PI_CAMERA", "true")
    monkeypatch.setenv("VISION_CAMERA_ID", "3")
    monkeypatch.setenv("VISION_FRAME_SOURCE", "/tmp/clip.mp4")
    monkeypatch.setenv("VISION_STATE_POLL_SECONDS", "4.5")
    monkeypatch.setenv("VISION_EVENT_COOLDOWN_SECONDS", "15")
    monkeypatch.setenv("VISION_SHOW_WINDOW", "yes")

    loaded = settings.load_settings()
    assert loaded.feature_pi_camera is True
    assert loaded.camera_id == 3
    assert loaded.frame_source == "/tmp/clip.mp4"
    assert loaded.state_poll_seconds == 4.5
    assert loaded.event_cooldown_seconds == 15.0
    assert loaded.show_window is True
