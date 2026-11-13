"""Unit tests for the optional OpenCV preview. No real display."""

from __future__ import annotations

import logging

from fakes import FakeCv2, FakeFrame

from preview_window import WINDOW_TITLE, PreviewWindow


def test_disabled_preview_is_noop():
    backend = FakeCv2()
    preview = PreviewWindow(enabled=False, backend=backend)

    preview.show(FakeFrame(), [("person", 0.9)])
    preview.close()

    assert backend.imshow_calls == []
    assert backend.destroy_calls == 0


def test_show_draws_labels_and_waits():
    backend = FakeCv2()
    frame = FakeFrame("live")
    preview = PreviewWindow(enabled=True, backend=backend)

    preview.show(frame, [("person", 0.91), ("car", 0.42)])

    assert frame.copy_count == 1
    assert len(backend.imshow_calls) == 1
    title, shown = backend.imshow_calls[0]
    assert title == WINDOW_TITLE
    assert shown.tag == "live-copy"
    assert backend.wait_key_calls == [1]
    texts = [call[1] for call in backend.put_text_calls]
    assert texts == ["person 0.91", "car 0.42"]


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
        preview.show(FakeFrame(), [("person", 0.5)])
        preview.show(FakeFrame(), [("person", 0.5)])

    assert len(backend.imshow_calls) == 0
    assert any("unavailable" in record.message.lower() for record in caplog.records)
