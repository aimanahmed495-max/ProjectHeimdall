"""Tests for the Bluesky watchlist adapter. Network calls are mocked."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests
from bluesky_adapter import BlueskyAdapter
from osint_settings import bluesky_enabled

FIXTURE = Path(__file__).parent / "fixtures" / "bluesky_author_feed.json"
NOW = datetime(2026, 10, 8, 18, 0, tzinfo=timezone.utc)
NORMAL_URI = "at://did:plc:watchlisttest/app.bsky.feed.post/normal1"


class FakeResponse:
    """Stand-in for ``requests.Response`` with a fixed JSON body."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = payload if isinstance(payload, str) else json.dumps(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(f"status {self.status_code}")
            error.response = self
            raise error

    def json(self):
        if isinstance(self._payload, str):
            return json.loads(self._payload)
        return self._payload


def load_fixture():
    """Return the synthetic getAuthorFeed body."""

    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def adapter_for(actors=("watchlist.test",), **kwargs):
    """Build an adapter frozen at ``NOW``."""

    defaults = {
        "appview": "https://public.api.bsky.app",
        "actors": actors,
        "clock": lambda: NOW,
    }
    defaults.update(kwargs)
    return BlueskyAdapter(**defaults)


def test_normal_post_becomes_source_item(monkeypatch):
    """A normal post keeps the at:// uri, stripped text, and indexedAt."""

    monkeypatch.setattr(
        "bluesky_adapter.requests.get",
        lambda url, timeout: FakeResponse(load_fixture()),
    )
    adapter = adapter_for()

    items = list(adapter.poll())

    assert len(items) == 1
    assert items[0].external_id == NORMAL_URI
    assert items[0].text == "Gun reported near the campus gate"
    assert items[0].timestamp == datetime(2026, 10, 8, 17, 55, tzinfo=timezone.utc)
    assert items[0].source_name == "bluesky-watchlist"


def test_skips_repost_pin_nonpost_empty_private_and_old(monkeypatch):
    """Reposts, pins, non-posts, empty text, private labels, and old posts drop."""

    monkeypatch.setattr(
        "bluesky_adapter.requests.get",
        lambda url, timeout: FakeResponse(load_fixture()),
    )
    adapter = adapter_for()

    items = list(adapter.poll())

    assert [item.external_id for item in items] == [NORMAL_URI]


def test_second_poll_yields_nothing(monkeypatch):
    """Dedup remembers uris across polls."""

    monkeypatch.setattr(
        "bluesky_adapter.requests.get",
        lambda url, timeout: FakeResponse(load_fixture()),
    )
    adapter = adapter_for()

    first = list(adapter.poll())
    second = list(adapter.poll())

    assert len(first) == 1
    assert second == []


def test_request_url_limit_filter_timeout_and_no_auth(monkeypatch):
    """The GET uses the AppView path, limit 25, posts_no_replies, and no auth."""

    captured = {}

    def fake_get(url, timeout, **kwargs):
        captured["url"] = url
        captured["timeout"] = timeout
        captured["kwargs"] = kwargs
        captured["headers"] = kwargs.get("headers")
        return FakeResponse({"feed": []})

    monkeypatch.setattr("bluesky_adapter.requests.get", fake_get)
    adapter = adapter_for(actors=("demo.handle.test",))

    list(adapter.poll())

    url = captured["url"]
    assert url.startswith(
        "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?"
    )
    assert "actor=demo.handle.test" in url
    assert "limit=25" in url
    assert "filter=posts_no_replies" in url
    assert captured["timeout"] == 10
    assert captured["headers"] is None
    assert "Authorization" not in url


def test_one_actor_http_error_skips_other_still_returns(monkeypatch, caplog):
    """HTTP 400 on one actor is logged; the other actor's posts still come through."""

    def fake_get(url, timeout):
        if "actor=bad.test" in url:
            return FakeResponse({"error": "ProfileNotFound"}, status_code=400)
        return FakeResponse(load_fixture())

    monkeypatch.setattr("bluesky_adapter.requests.get", fake_get)
    adapter = adapter_for(actors=("bad.test", "watchlist.test"))

    with caplog.at_level(logging.WARNING):
        items = list(adapter.poll())

    assert len(items) == 1
    assert items[0].external_id == NORMAL_URI
    assert "bad.test" in caplog.text
    assert "400" in caplog.text


def test_every_actor_failure_raises(monkeypatch):
    """When every actor fails, the last RequestException is re-raised."""

    def fake_get(url, timeout):
        return FakeResponse({"error": "ProfileNotFound"}, status_code=400)

    monkeypatch.setattr("bluesky_adapter.requests.get", fake_get)
    adapter = adapter_for(actors=("a.test", "b.test"))

    with pytest.raises(requests.HTTPError):
        list(adapter.poll())


def test_invalid_json_or_missing_feed_yields_nothing(monkeypatch):
    """Bad JSON and a non-list feed produce no items."""

    class BadJsonResponse(FakeResponse):
        def json(self):
            raise ValueError("not json")

    monkeypatch.setattr(
        "bluesky_adapter.requests.get",
        lambda url, timeout: BadJsonResponse("not-json"),
    )
    assert list(adapter_for().poll()) == []

    monkeypatch.setattr(
        "bluesky_adapter.requests.get",
        lambda url, timeout: FakeResponse({"feed": "nope"}),
    )
    assert list(adapter_for().poll()) == []


def test_from_env_validates_and_trims_actors(monkeypatch):
    """Empty actors and more than ten raise; whitespace entries are trimmed."""

    monkeypatch.setenv("BLUESKY_APPVIEW_URL", " https://public.api.bsky.app/ ")
    monkeypatch.setenv("BLUESKY_ACTORS", "")
    with pytest.raises(ValueError, match="BLUESKY_ACTORS is not set"):
        BlueskyAdapter.from_env()

    monkeypatch.setenv(
        "BLUESKY_ACTORS",
        ",".join(f"actor{i}.test" for i in range(11)),
    )
    with pytest.raises(ValueError, match="more than 10"):
        BlueskyAdapter.from_env()

    monkeypatch.setenv("BLUESKY_ACTORS", " a.test , , b.test ")
    adapter = BlueskyAdapter.from_env()
    assert adapter._actors == ["a.test", "b.test"]
    assert adapter._appview == "https://public.api.bsky.app"
    payload = adapter.registration_payload()
    assert payload["source_type"] == "Social Media"
    assert payload["reliability_score"] == 0.5
    assert payload["url"].endswith("/xrpc/app.bsky.feed.getAuthorFeed")


def test_bluesky_enabled_defaults_to_false(monkeypatch):
    """An unset FEATURE_BLUESKY keeps the adapter off."""

    monkeypatch.delenv("FEATURE_BLUESKY", raising=False)
    assert bluesky_enabled() is False
    monkeypatch.setenv("FEATURE_BLUESKY", "true")
    assert bluesky_enabled() is True
