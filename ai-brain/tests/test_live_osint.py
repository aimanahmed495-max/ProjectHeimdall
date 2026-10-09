"""Live-loop tests. HTTP and the LLM are fakes; ChatGroq is never constructed."""

import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from camera_activation import CameraActivator
from corroboration import CorroborationTracker
from keyword_filter import KeywordFilter
from live_osint import LiveOsintRunner
from main import OsintIngestionApp
from ntfy_adapter import NtfyAdapter
from osint_client import HeimdallAPIClient, HeimdallAPIError
from osint_settings import live_osint_enabled
from rss_adapter import RssAdapter
from source_adapter import SourceAdapter, SourceItem

NOW = datetime(2026, 10, 8, 18, 0, tzinfo=timezone.utc)
STAMP = datetime(2026, 10, 8, 18, 5, tzinfo=timezone.utc)


class FakeAgent:
    """Classifier stand-in used by the mock ingestion path."""

    calls = []

    def __init__(self, client):
        self.client = client

    def run(self, alert_text, source_id):
        FakeAgent.calls.append((alert_text, source_id))
        return {
            "alert_text": alert_text,
            "source_id": source_id,
            "object_class": "person",
            "confidence_score": 0.5,
            "threat_event": {"event_id": 1},
            "system_log": {"log_id": 1},
            "error": None,
        }


class ScriptedAgent:
    """Returns a fixed category and incrementing threat-event ids."""

    def __init__(self):
        self._ids = iter([11, 22, 33])
        self.calls = []

    def run(self, alert_text, source_id):
        self.calls.append((alert_text, source_id))
        return {
            "object_class": "weapon",
            "threat_event": {"event_id": next(self._ids)},
            "error": None,
        }


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


def item(source_name, text, external_id, timestamp):
    """Build one source item."""

    return SourceItem(source_name, text, timestamp, external_id)


def response(status_code, payload):
    """Build a mocked HTTP response."""

    mocked = Mock()
    mocked.status_code = status_code
    mocked.json.return_value = payload
    mocked.text = str(payload)
    mocked.request.method = "PATCH"
    mocked.url = "http://localhost:8000"
    return mocked


def registered_client(rows):
    """Return a client mock that already lists ``rows``."""

    client = Mock()
    client.list_sources.return_value = rows
    return client


def runner_for(client, agent, adapters, **kwargs):
    """Build a runner that does not sleep between polls."""

    defaults = {
        "keyword_filter": KeywordFilter(["gun"]),
        "tracker": CorroborationTracker(window_seconds=300),
        "activator": CameraActivator(client, camera_id=1, clock=lambda: STAMP),
        "poll_interval": 5,
        "sleep": lambda _delay: None,
    }
    defaults.update(kwargs)
    return LiveOsintRunner(
        client=client,
        agent=agent,
        adapters=adapters,
        **defaults,
    )


def test_keyword_match_and_case(monkeypatch):
    """Keywords match case-insensitively and ignore unrelated text."""

    monkeypatch.delenv("OSINT_KEYWORDS", raising=False)
    default_filter = KeywordFilter.from_env()
    assert default_filter.matches("Shots were reported")
    assert not default_filter.matches("sunny afternoon")

    monkeypatch.setenv("OSINT_KEYWORDS", "drone, laser")
    custom = KeywordFilter.from_env()
    assert custom.matches("A DRONE overhead")
    assert not custom.matches("shots fired")


def test_keyword_miss_is_logged(caplog):
    """Text with no keyword is logged and removed before classification."""

    missed = item("local-rss-feed", "sunny afternoon", "sun-1", NOW)
    filt = KeywordFilter(["gun"])

    with caplog.at_level(logging.INFO):
        assert filt.keep([missed]) == []

    assert "sun-1" in caplog.text
    assert "no keyword match" in caplog.text


def test_keyword_filter_drops_items_before_the_agent(caplog):
    """The agent runs only for items that match a keyword."""

    adapter = StaticAdapter(
        "alpha-source",
        [
            [
                item("alpha-source", "sunny afternoon", "sun-1", NOW),
                item("alpha-source", "GUN seen at the gate", "gun-1", NOW),
            ]
        ],
    )
    client = registered_client(
        [{"source_id": 1, "source_name": "alpha-source"}],
    )
    agent = ScriptedAgent()
    live = runner_for(client, agent, [adapter])

    with caplog.at_level(logging.INFO):
        assert live.run(max_cycles=1) == 0

    assert agent.calls == [("GUN seen at the gate", 1)]
    assert "no keyword match" in caplog.text
    client.put_camera_state.assert_not_called()
    client.patch_threat_event.assert_not_called()


def test_single_report_does_not_change_the_camera():
    """One matching report is classified and leaves the camera alone."""

    adapter = StaticAdapter(
        "alpha-source",
        [[item("alpha-source", "gun reported", "g1", NOW)]],
    )
    client = registered_client(
        [{"source_id": 1, "source_name": "alpha-source"}],
    )
    live = runner_for(client, ScriptedAgent(), [adapter])

    assert live.run(max_cycles=1) == 0

    client.patch_threat_event.assert_not_called()
    client.put_camera_state.assert_not_called()
    client.post_system_log.assert_not_called()


def test_activation_patches_then_puts_once():
    """Two sources corroborate once: PATCH, then PUT, then one system log."""

    adapter_a = StaticAdapter(
        "alpha-source",
        [
            [item("alpha-source", "gun near the gate", "a1", NOW)],
            [
                item(
                    "alpha-source",
                    "gun near the gate again",
                    "a2",
                    NOW + timedelta(seconds=20),
                )
            ],
        ],
    )
    adapter_b = StaticAdapter(
        "beta-source",
        [
            [
                item(
                    "beta-source",
                    "gun near the gate",
                    "b1",
                    NOW + timedelta(seconds=10),
                )
            ],
            [],
        ],
    )
    client = registered_client(
        [
            {"source_id": 1, "source_name": "alpha-source"},
            {"source_id": 2, "source_name": "beta-source"},
        ]
    )
    agent = ScriptedAgent()
    live = runner_for(client, agent, [adapter_a, adapter_b])

    assert live.run(max_cycles=2) == 0

    assert [source_id for _text, source_id in agent.calls] == [1, 2, 1]
    patched_ids = [call.args[0] for call in client.patch_threat_event.call_args_list]
    assert patched_ids == [11, 22]
    payload = {
        "status": "Corroborated",
        "corroborated_at": "2026-10-08T18:05:00Z",
    }
    for call in client.patch_threat_event.call_args_list:
        assert call.args[1] == payload
    client.put_camera_state.assert_called_once_with(
        1,
        {"mode": "Active", "fps": 5, "resolution": "720p"},
    )
    client.post_system_log.assert_called_once()
    log_entry = client.post_system_log.call_args.args[0]
    assert log_entry["event_id"] == 11
    assert log_entry["module"] == "osint-agent"
    assert "Active" in log_entry["message"]
    assert "weapon" in log_entry["message"]
    activation = [
        name
        for name, _args, _kwargs in client.method_calls
        if name in {"patch_threat_event", "put_camera_state", "post_system_log"}
    ]
    assert activation == [
        "patch_threat_event",
        "patch_threat_event",
        "put_camera_state",
        "post_system_log",
    ]


def test_registration_reuses_existing_sources():
    """Startup lists sources first and does not POST names that already exist."""

    client = registered_client(
        [
            {"source_id": 4, "source_name": "ntfy-tipline"},
            {"source_id": 5, "source_name": "local-rss-feed"},
        ]
    )
    adapters = [
        NtfyAdapter(server="https://ntfy.sh", topic="heimdall-demo-change-me"),
        RssAdapter(feed_url="http://localhost:8001/feed.xml"),
    ]
    live = runner_for(client, Mock(), adapters)

    assert live.register_sources() == {
        "ntfy-tipline": 4,
        "local-rss-feed": 5,
    }
    client.list_sources.assert_called_once()
    client.register_source.assert_not_called()


def test_registration_posts_only_missing_sources():
    """A source missing from GET /sources is created once."""

    client = registered_client(
        [{"source_id": 4, "source_name": "ntfy-tipline"}],
    )
    client.register_source.return_value = {
        "source_id": 9,
        "source_name": "local-rss-feed",
        "already_registered": False,
    }
    adapters = [
        NtfyAdapter(server="https://ntfy.sh", topic="heimdall-demo-change-me"),
        RssAdapter(feed_url="http://localhost:8001/feed.xml"),
    ]
    live = runner_for(client, Mock(), adapters)

    mapping = live.register_sources()

    client.register_source.assert_called_once()
    posted = client.register_source.call_args.args[0]
    assert posted["source_name"] == "local-rss-feed"
    assert posted["source_type"] == "RSS"
    assert posted["url"] == "http://localhost:8001/feed.xml"
    assert 0 <= posted["reliability_score"] <= 1
    assert mapping == {"ntfy-tipline": 4, "local-rss-feed": 9}


def test_flag_off_uses_the_mock_path(monkeypatch):
    """The default flag processes mock JSON and does not start live polling."""

    monkeypatch.setenv("FEATURE_LIVE_OSINT", "false")
    FakeAgent.calls = []

    def reject_live(**_kwargs):
        raise AssertionError("live path should stay disabled")

    monkeypatch.setattr("main.OsintAgent", FakeAgent)
    monkeypatch.setattr("main.LiveOsintRunner", reject_live)
    app = OsintIngestionApp()
    app._client = Mock()
    app._client.base_url = "http://localhost:8000"

    def register(source):
        return {
            "source_name": source["source_name"],
            "source_id": len(app._client.register_source.mock_calls),
            "already_registered": False,
        }

    app._client.register_source.side_effect = register

    assert app.run() == 0
    assert len(FakeAgent.calls) == 5
    assert any("break-in" in text for text, _source_id in FakeAgent.calls)
    registered = [
        call.args[0]["source_name"]
        for call in app._client.register_source.call_args_list
    ]
    assert "District 4 Police Scanner" in registered
    assert "ntfy-tipline" not in registered
    app._client.put_camera_state.assert_not_called()


def test_flag_on_uses_the_live_runner(monkeypatch):
    """The flag skips mock alerts and hands control to the live runner."""

    monkeypatch.setenv("FEATURE_LIVE_OSINT", "true")
    FakeAgent.calls = []
    runner = Mock()
    runner.run.return_value = 0
    constructed = {}

    def build_runner(**kwargs):
        constructed.update(kwargs)
        return runner

    monkeypatch.setattr("main.OsintAgent", FakeAgent)
    monkeypatch.setattr("main.LiveOsintRunner", build_runner)
    app = OsintIngestionApp()
    app._client = Mock()
    app._client.base_url = "http://localhost:8000"

    assert app.run() == 0
    runner.run.assert_called_once()
    app._client.authenticate.assert_called_once()
    assert isinstance(constructed["agent"], FakeAgent)
    assert FakeAgent.calls == []
    app._client.register_source.assert_not_called()


def test_live_flag_defaults_to_off(monkeypatch):
    """An unset flag keeps mock ingestion enabled."""

    monkeypatch.delenv("FEATURE_LIVE_OSINT", raising=False)
    assert live_osint_enabled() is False
    monkeypatch.setenv("FEATURE_LIVE_OSINT", "true")
    assert live_osint_enabled() is True


def test_default_adapters_poll_ntfy_and_rss(monkeypatch):
    """With the flag's runner defaults, both public sources are polled."""

    monkeypatch.setenv("NTFY_SERVER", "https://ntfy.sh")
    monkeypatch.setenv("NTFY_TOPIC", "heimdall-demo-change-me")
    monkeypatch.setenv("RSS_FEED_URL", "http://localhost:8001/feed.xml")
    urls = []

    def fake_get(url, timeout):
        urls.append((url, timeout))
        if "feed.xml" in url:
            text = "<rss><channel></channel></rss>"
        else:
            text = ""
        response = Mock()
        response.text = text
        response.raise_for_status.return_value = None
        return response

    monkeypatch.setattr("ntfy_adapter.requests.get", fake_get)
    monkeypatch.setattr("rss_adapter.requests.get", fake_get)
    client = registered_client(
        [
            {"source_id": 4, "source_name": NtfyAdapter.SOURCE_NAME},
            {"source_id": 5, "source_name": RssAdapter.SOURCE_NAME},
        ]
    )
    agent = Mock()
    live = LiveOsintRunner(
        client=client,
        agent=agent,
        poll_interval=5,
        sleep=lambda _delay: None,
        keyword_filter=KeywordFilter(["gun"]),
    )

    assert live.run(max_cycles=1) == 0

    requested = [url for url, _timeout in urls]
    assert any(
        "ntfy.sh" in url and "poll=1" in url and "since=10m" in url
        for url in requested
    )
    assert "http://localhost:8001/feed.xml" in requested
    agent.run.assert_not_called()


def test_client_patch_put_and_list_use_backend_routes():
    """Corroboration uses the threat PATCH and camera PUT routes."""

    client = HeimdallAPIClient(
        base_url="http://localhost:8000",
        username="osint.service",
        password="test-password-not-used",
    )
    client._request = Mock(
        side_effect=[
            response(200, {"event_id": 7, "status": "Corroborated"}),
            response(200, {"camera_id": 1, "mode": "Active"}),
            response(200, [{"source_id": 4, "source_name": "ntfy-tipline"}]),
        ]
    )
    update = {
        "status": "Corroborated",
        "corroborated_at": "2026-10-08T18:00:00Z",
    }
    camera = {"mode": "Active", "fps": 5, "resolution": "720p"}

    client.patch_threat_event(7, update)
    client.put_camera_state(1, camera)
    listed = client.list_sources()

    assert client._request.call_args_list[0].args == (
        "PATCH",
        "/threat-events/7",
    )
    assert client._request.call_args_list[0].kwargs["json_body"] == update
    assert client._request.call_args_list[1].args == (
        "PUT",
        "/camera-states/1",
    )
    assert client._request.call_args_list[1].kwargs["json_body"] == camera
    assert client._request.call_args_list[2].args == ("GET", "/sources")
    assert listed[0]["source_name"] == "ntfy-tipline"


def test_list_sources_rejects_a_non_list():
    """A malformed sources payload is an API error, not a crash later."""

    client = HeimdallAPIClient(
        base_url="http://localhost:8000",
        username="osint.service",
        password="test-password-not-used",
    )
    client._request = Mock(return_value=response(200, {"source_id": 1}))

    with pytest.raises(HeimdallAPIError, match="not a list"):
        client.list_sources()
