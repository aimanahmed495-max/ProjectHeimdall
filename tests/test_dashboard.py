from pathlib import Path

from streamlit.testing.v1 import AppTest


CONSOLE_PATH = Path("frontend/heimdall_console.html")


def test_streamlit_host_renders_without_python_errors() -> None:
    dashboard = AppTest.from_file("frontend/app.py")
    dashboard.run(timeout=10)

    assert not dashboard.exception


def test_console_contains_live_backend_integration() -> None:
    console = CONSOLE_PATH.read_text(encoding="utf-8")

    assert "Heimdall backend" in console
    assert "new WebSocket(WS_URL)" in console
    assert "alert.created" in console
    assert 'id="demoBtn"' in console
    assert "/api/demo/alerts" in console
