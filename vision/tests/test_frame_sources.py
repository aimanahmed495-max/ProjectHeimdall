"""Unit tests for frame sources and the builder."""

from __future__ import annotations

from pathlib import Path

import pytest
from fakes import FakeCapture, make_settings

from frame_sources import (
    PI_CAMERA_MESSAGE,
    PiCameraSource,
    StaticImageSource,
    VideoCaptureSource,
    build_frame_source,
)


def test_build_frame_source_webcam_index():
    settings = make_settings(frame_source="0", feature_pi_camera=False)
    source = build_frame_source(settings)
    assert isinstance(source, VideoCaptureSource)
    assert source._target == "0"
    assert source._is_file is False


def test_build_frame_source_video_file(tmp_path: Path):
    clip = tmp_path / "demo.mp4"
    clip.write_bytes(b"not-a-real-video")
    source = build_frame_source(
        make_settings(frame_source=str(clip), feature_pi_camera=False)
    )
    assert isinstance(source, VideoCaptureSource)
    assert source._is_file is True


def test_build_frame_source_image_directory(tmp_path: Path):
    source = build_frame_source(
        make_settings(frame_source=str(tmp_path), feature_pi_camera=False)
    )
    assert isinstance(source, StaticImageSource)


def test_build_frame_source_pi_flag():
    source = build_frame_source(make_settings(feature_pi_camera=True))
    assert isinstance(source, PiCameraSource)


def test_pi_camera_open_raises_t18_message():
    source = PiCameraSource()
    with pytest.raises(RuntimeError, match="T18"):
        source.open()
    assert source.is_open is False
    assert "T18" in PI_CAMERA_MESSAGE


def test_video_capture_fails_clearly_when_not_opened():
    def factory(_target):
        return FakeCapture(opened=False)

    source = VideoCaptureSource("0", capture_factory=factory)
    with pytest.raises(RuntimeError, match="Could not open"):
        source.open()
    assert source.is_open is False


def test_video_capture_loops_file_at_end():
    frames = ["a", "b"]
    capture = FakeCapture(frames=frames)

    def factory(_target):
        return capture

    source = VideoCaptureSource("/tmp/demo.mp4", capture_factory=factory)
    source.open()
    assert source.read() == ("frame-1", "a")
    assert source.read() == ("frame-2", "b")
    again = source.read()
    assert again == ("frame-3", "a")
    assert capture.set_calls == [(1, 0)]
    source.close()
    assert capture.release_calls == 1
    assert source.is_open is False
    assert source.read() is None


def test_static_image_source_lifecycle(tmp_path: Path, monkeypatch):
    image = tmp_path / "one.jpg"
    image.write_bytes(b"fake")

    class FakeCv2:
        @staticmethod
        def imread(_path):
            return "fake-frame"

    monkeypatch.setitem(__import__("sys").modules, "cv2", FakeCv2())

    source = StaticImageSource(tmp_path)
    assert source.is_open is False
    source.open()
    assert source.is_open is True
    assert source.read() == ("one.jpg", "fake-frame")
    assert source.read() == ("one.jpg", "fake-frame")  # loops
    source.close()
    assert source.is_open is False
    assert source.read() is None
