"""Structured logging tests. HTTP and the LLM are fakes; no network."""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
import requests
from osint_client import HeimdallAPIClient, HeimdallAPIError
from osint_logging import JsonFormatter, configure_logging, log_context
from test_live_osint import (
    NOW,
    ScriptedAgent,
    StaticAdapter,
    item,
    registered_client,
    response,
    runner_for,
)

USER_ID = 7
REQUIRED = ("timestamp", "level", "request_id", "user_id")


def events(caplog, name):
    """Return formatted JSON payloads for records with ``event == name``."""

    formatter = JsonFormatter()
    return [
        json.loads(formatter.format(record))
        for record in caplog.records
        if getattr(record, "event", None) == name
    ]


def assert_required_fields(payload, level):
    """Every pipeline event carries timestamp, level, request_id, user_id."""

    for field in REQUIRED:
        assert field in payload
    datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
    assert payload["timestamp"].endswith("Z")
    assert payload["level"] == level
    assert isinstance(payload["request_id"], str) and payload["request_id"]
    assert payload["user_id"] == USER_ID


def one_source(batches, agent=None, **kwargs):
    """Build a runner over a single ``alpha-source`` adapter."""

    adapter = StaticAdapter("alpha-source", batches)
    client = registered_client([{"source_id": 1, "source_name": "alpha-source"}])
    return runner_for(client, agent or ScriptedAgent(), [adapter], **kwargs)


def two_sources(client):
    """Build a runner whose two sources corroborate on the second report."""

    adapter_a = StaticAdapter(
        "alpha-source",
        [[item("alpha-source", "gun near the gate", "a1", NOW)]],
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
            ]
        ],
    )
    return runner_for(
        client,
        ScriptedAgent(),
        [adapter_a, adapter_b],
        user_id=USER_ID,
    )


def two_source_client():
    """Return a client that lists both corroborating sources."""

    return registered_client(
        [
            {"source_id": 1, "source_name": "alpha-source"},
            {"source_id": 2, "source_name": "beta-source"},
        ]
    )


class FailingAdapter(StaticAdapter):
    """Raises a request error on every poll."""

    def _fetch_items(self):
        raise requests.ConnectionError("feed unreachable")


class RaisingAgent:
    """Agent whose API call fails."""

    def run(self, alert_text, source_id):
        raise HeimdallAPIError("POST /threat-events failed (500)")


class FailedClassificationAgent:
    """Agent that returns a classification error instead of raising."""

    def run(self, alert_text, source_id):
        return {"error": "Groq classification failed: timeout"}


def test_classify_event_has_required_fields(caplog):
    """A classified item emits one JSON classify event with every field."""

    live = one_source(
        [[item("alpha-source", "gun reported", "g1", NOW)]],
        user_id=USER_ID,
    )

    with caplog.at_level(logging.INFO):
        assert live.run(max_cycles=1) == 0

    [payload] = events(caplog, "classify")
    assert_required_fields(payload, "INFO")
    assert payload["event"] == "classify"
    assert payload["object_class"] == "weapon"
    assert payload["event_id"] == 11
    assert payload["source_id"] == 1
    assert payload["external_id"] == "g1"


def test_failed_classification_is_a_warning(caplog):
    """An agent error result is logged as a classify warning with fields."""

    live = one_source(
        [[item("alpha-source", "gun reported", "g1", NOW)]],
        agent=FailedClassificationAgent(),
        user_id=USER_ID,
    )

    with caplog.at_level(logging.INFO):
        live.run(max_cycles=1)

    [payload] = events(caplog, "classify")
    assert_required_fields(payload, "WARNING")
    assert "timeout" in payload["error"]


def test_corroborate_event_has_required_fields(caplog):
    """Corroboration logs the category, event ids, and source ids."""

    live = two_sources(two_source_client())

    with caplog.at_level(logging.INFO):
        assert live.run(max_cycles=1) == 0

    [payload] = events(caplog, "corroborate")
    assert_required_fields(payload, "INFO")
    # Tracker normalizes free-form labels; ScriptedAgent still emits "weapon".
    assert payload["category"] == "unknown"
    assert payload["event_ids"] == [11, 22]
    assert payload["source_ids"] == [1, 2]
    triggering = events(caplog, "classify")[-1]
    assert payload["request_id"] == triggering["request_id"]


def test_each_item_gets_its_own_request_id(caplog):
    """Two items in one poll are logged under different request ids."""

    live = one_source(
        [
            [
                item("alpha-source", "gun one", "g1", NOW),
                item("alpha-source", "gun two", "g2", NOW),
            ]
        ],
        user_id=USER_ID,
    )

    with caplog.at_level(logging.INFO):
        live.run(max_cycles=1)

    ids = [payload["request_id"] for payload in events(caplog, "classify")]
    assert len(ids) == 2
    assert ids[0] != ids[1]


def test_poll_error_event_has_required_fields(caplog):
    """A source request error is logged and the other source still runs."""

    failing = FailingAdapter("alpha-source", [])
    healthy = StaticAdapter(
        "beta-source",
        [[item("beta-source", "gun reported", "b1", NOW)]],
    )
    agent = ScriptedAgent()
    live = runner_for(
        two_source_client(),
        agent,
        [failing, healthy],
        user_id=USER_ID,
    )

    with caplog.at_level(logging.INFO):
        assert live.run(max_cycles=1) == 0

    [payload] = events(caplog, "error")
    assert_required_fields(payload, "ERROR")
    assert payload["stage"] == "poll"
    assert payload["source"] == "alpha-source"
    assert payload["error_type"] == "ConnectionError"
    assert agent.calls == [("gun reported", 2)]


def test_agent_error_event_has_required_fields(caplog):
    """An API error raised by the agent is logged as a classify-stage error."""

    live = one_source(
        [[item("alpha-source", "gun reported", "g1", NOW)]],
        agent=RaisingAgent(),
        user_id=USER_ID,
    )

    with caplog.at_level(logging.INFO):
        assert live.run(max_cycles=1) == 0

    [payload] = events(caplog, "error")
    assert_required_fields(payload, "ERROR")
    assert payload["stage"] == "classify"
    assert payload["source_id"] == 1
    assert payload["error_type"] == "HeimdallAPIError"


def test_activation_error_event_has_required_fields(caplog):
    """A failed activation logs a corroborate-stage error, not a success."""

    client = two_source_client()
    client.put_camera_state.side_effect = HeimdallAPIError("PUT failed (500)")
    live = two_sources(client)

    with caplog.at_level(logging.INFO):
        assert live.run(max_cycles=1) == 0

    assert events(caplog, "corroborate") == []
    [payload] = events(caplog, "error")
    assert_required_fields(payload, "ERROR")
    assert payload["stage"] == "corroborate"
    # Tracker normalizes free-form labels; ScriptedAgent still emits "weapon".
    assert payload["category"] == "unknown"


def test_console_banner_is_unchanged(capsys, caplog):
    """The source banner still prints to stdout; events do not."""

    live = one_source(
        [[item("alpha-source", "gun reported", "g1", NOW)]],
        user_id=USER_ID,
    )

    with caplog.at_level(logging.INFO):
        live.run(max_cycles=1)

    captured = capsys.readouterr()
    assert captured.out == "Live sources:\n  alpha-source (id=1)\n\n"
    assert captured.err == ""


def test_formatter_uses_bound_context_for_plain_records():
    """Records not built by log_event still get the ids bound at format time."""

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "hi", None, None)

    with log_context(request_id="req-1", user_id=USER_ID):
        payload = json.loads(JsonFormatter().format(record))
    after = json.loads(JsonFormatter().format(record))

    assert payload["request_id"] == "req-1"
    assert payload["user_id"] == USER_ID
    assert after["request_id"] is None
    assert after["user_id"] is None


def test_configure_logging_installs_json_handler():
    """With no handlers configured, the root logger writes JSON lines."""

    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    root.handlers = []
    try:
        configure_logging()
        [handler] = root.handlers
        assert isinstance(handler.formatter, JsonFormatter)
        assert root.level == logging.INFO
    finally:
        root.handlers = saved_handlers
        root.setLevel(saved_level)


def client_with(result):
    """Return an API client whose next request yields ``result``."""

    client = HeimdallAPIClient(
        base_url="http://localhost:8000",
        username="osint.service",
        password="test-password-not-used",
    )
    client._request = Mock(**result)
    return client


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        ({"return_value": response(200, {"user_id": 3})}, 3),
        ({"return_value": response(401, {"detail": "nope"})}, None),
        ({"return_value": response(200, {"user_id": "3"})}, None),
        ({"side_effect": HeimdallAPIError("down")}, None),
    ],
)
def test_current_user_id(result, expected):
    """``GET /auth/me`` supplies the user id; failures return None."""

    client = client_with(result)

    assert client.current_user_id() == expected
    client._request.assert_called_once_with("GET", "/auth/me")
