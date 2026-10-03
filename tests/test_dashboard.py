from pathlib import Path

from streamlit.testing.v1 import AppTest


CONSOLE_PATH = Path("frontend/heimdall_console.html")


def test_streamlit_host_renders_without_python_errors() -> None:
    dashboard = AppTest.from_file("frontend/app.py")
    dashboard.run(timeout=10)

    assert not dashboard.exception


def test_console_contains_core_backend_configuration() -> None:
    """Static checks only; does not execute browser requests."""
    console = CONSOLE_PATH.read_text(encoding="utf-8")

    # Preserve the configurable API address and original dashboard views.
    assert "__HEIMDALL_API_URL__" in console
    for view_id in ("viewFeed", "viewCams", "viewIntel", "viewHistory"):
        assert f'id="{view_id}"' in console

    # Core backend collections and session verification.
    for endpoint in (
        "/auth/me",
        "/sources",
        "/threat-events",
        "/alert-logs",
        "/camera-states",
        "/system-logs",
    ):
        assert endpoint in console

    # The original console must no longer call the demo API.
    assert "/api/demo/alerts" not in console
    assert "new WebSocket(WS_URL)" not in console