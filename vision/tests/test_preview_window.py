"""Unit tests for the optional OpenCV preview. No real display."""

from __future__ import annotations

import logging

from fakes import FakeCv2, FakeFrame

from preview_window import (
    _COLOR_GREEN,
    _COLOR_RED,
    _COLOR_YELLOW,
    WINDOW_TITLE,
    PreviewWindow,
)


def test_disabled_preview_is_noop():
    backend = FakeCv2()
    preview = PreviewWindow(enabled=False, backend=backend)

    preview.show(FakeFrame(), [("person", 0.9, 1.0, 2.0, 3.0, 4.0)])
    preview.close()

    assert backend.imshow_calls == []
    assert backend.destroy_calls == 0


def test_show_draws_boxes_labels_and_waits():
    backend = FakeCv2()
    frame = FakeFrame("live")
    preview = PreviewWindow(enabled=True, backend=backend)

    preview.show(
        frame,
        [
            ("person", 0.91, 10.0, 20.0, 100.0, 200.0),
            ("car", 0.70, 30.0, 40.0, 130.0, 140.0),
            ("dog", 0.55, 5.0, 6.0, 50.0, 60.0),
        ],
    )

    assert frame.copy_count == 1
    assert len(backend.imshow_calls) == 1
    title, shown = backend.imshow_calls[0]
    assert title == WINDOW_TITLE
    assert shown.tag == "live-copy"
    assert backend.wait_key_calls == [1]

    assert len(backend.rectangle_calls) == 3
    assert backend.rectangle_calls[0][1:] == ((10, 20), (100, 200), _COLOR_GREEN, 2)
    assert backend.rectangle_calls[1][1:] == ((30, 40), (130, 140), _COLOR_YELLOW, 2)
    assert backend.rectangle_calls[2][1:] == ((5, 6), (50, 60), _COLOR_RED, 2)

    texts = [call[1] for call in backend.put_text_calls]
    colors = [call[5] for call in backend.put_text_calls]
    assert texts == ["person 0.91", "car 0.70", "dog 0.55"]
    assert colors == [_COLOR_GREEN, _COLOR_YELLOW, _COLOR_RED]


def test_close_destroys_window_after_show():
    backend = FakeCv2()
    preview = PreviewWindow(enabled=True, backend=backend)

    preview.show(FakeFrame(), [])
    preview.close()
    preview.close()

    assert backend.destroy_calls == 1


def test_unavailable_display_logs_warning_and_skips(caplog):
    backend = FakeCv2()
    backend.imshow_error = RuntimeError("function not implemented")
    preview = PreviewWindow(enabled=True, backend=backend)

    with caplog.at_level(logging.WARNING):
        preview.show(FakeFrame(), [("person", 0.5, 1.0, 2.0, 3.0, 4.0)])
        preview.show(FakeFrame(), [("person", 0.5, 1.0, 2.0, 3.0, 4.0)])

    assert len(backend.imshow_calls) == 0
    assert any("unavailable" in record.message.lower() for record in caplog.records)


def test_color_bands():
    assert PreviewWindow._color_for_confidence(0.80) == _COLOR_GREEN
    assert PreviewWindow._color_for_confidence(0.79) == _COLOR_YELLOW
    assert PreviewWindow._color_for_confidence(0.65) == _COLOR_YELLOW
    assert PreviewWindow._color_for_confidence(0.64) == _COLOR_RED
