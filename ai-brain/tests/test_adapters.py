"""Tests for ntfy, RSS, and the local demo feed. Network calls are mocked."""

from datetime import datetime, timezone

import requests
from demo_feed import DemoFeedStore, build_form_page, build_rss
from ntfy_adapter import NtfyAdapter
from rss_adapter import RssAdapter

NOW = datetime(2026, 10, 8, 18, 0, tzinfo=timezone.utc)

NTFY_BODY = "\n".join(
    [
        "",
        "not-json",
        '{"id":"o1","event":"open","topic":"heimdall-demo-change-me"}',
        (
            '{"id":"m1","event":"message","topic":"heimdall-demo-change-me",'
            '"message":"Shots fired near the gate","time":1760000000}'
        ),
        (
            '{"id":"m1","event":"message","topic":"heimdall-demo-change-me",'
            '"message":"Shots fired near the gate","time":1760000000}'
        ),
        '{"id":"k1","event":"keepalive","topic":"heimdall-demo-change-me"}',
    ]
)

RSS_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>No id</title>
      <description>gun seen</description>
    </item>
    <item>
      <title>Gate</title>
      <description>Shots fired</description>
      <guid>rss-1</guid>
      <pubDate>Thu, 08 Oct 2026 18:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


class FakeResponse:
    """Stand-in for ``requests.Response`` with a fixed body."""

    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def test_ntfy_keeps_messages_and_skips_other_events(monkeypatch):
    """Message lines become items. Open, keepalive, and junk lines do not."""

    urls = []

    def fake_get(url, timeout):
        urls.append(url)
        return FakeResponse(NTFY_BODY)

    monkeypatch.setattr("ntfy_adapter.requests.get", fake_get)
    adapter = NtfyAdapter(server="https://ntfy.sh", topic="heimdall-demo-change-me")

    first = list(adapter.poll())
    second = list(adapter.poll())

    assert len(first) == 1
    assert first[0].external_id == "m1"
    assert first[0].source_name == "ntfy-tipline"
    assert first[0].text == "Shots fired near the gate"
    assert first[0].timestamp == datetime.fromtimestamp(1760000000, tz=timezone.utc)
    assert second == []
    assert "poll=1" in urls[0]
    assert "since=10m" in urls[0]
    assert urls[0].startswith(
        "https://ntfy.sh/heimdall-demo-change-me/json?"
    )
    assert "since=m1" in urls[1]
    assert "since=k1" not in urls[1]
    assert "since=o1" not in urls[1]


def test_rss_parses_guid_and_deduplicates(monkeypatch):
    """RSS items need a guid. A second poll of the same guid yields nothing."""

    monkeypatch.setattr(
        "rss_adapter.requests.get",
        lambda url, timeout: FakeResponse(RSS_BODY),
    )
    adapter = RssAdapter(feed_url="http://localhost:8001/feed.xml")

    first = list(adapter.poll())
    second = list(adapter.poll())

    assert len(first) == 1
    assert first[0].external_id == "rss-1"
    assert first[0].source_name == "local-rss-feed"
    assert "Gate" in first[0].text
    assert "Shots fired" in first[0].text
    assert first[0].timestamp == NOW
    assert second == []


def test_demo_feed_form_and_rss_round_trip(monkeypatch):
    """Submitted demo text is served as RSS and read back by the adapter."""

    store = DemoFeedStore()
    store.add("Shots fired near the gate")
    xml = build_rss(store.items())
    page = build_form_page()

    assert "Submit" in page
    assert 'name="text"' in page
    assert "<textarea" in page

    monkeypatch.setattr(
        "rss_adapter.requests.get",
        lambda url, timeout: FakeResponse(xml),
    )
    items = list(RssAdapter("http://localhost:8001/feed.xml").poll())

    assert len(items) == 1
    assert items[0].external_id == "demo-1"
    assert "Shots fired near the gate" in items[0].text


def test_rss_request_uses_the_configured_feed_url(monkeypatch):
    """The adapter GETs RSS_FEED_URL and does not stream the response."""

    seen = {}

    def fake_get(url, timeout):
        seen["url"] = url
        seen["timeout"] = timeout
        return FakeResponse("<rss><channel></channel></rss>")

    monkeypatch.setattr("rss_adapter.requests.get", fake_get)
    list(RssAdapter("http://localhost:8001/feed.xml").poll())

    assert seen["url"] == "http://localhost:8001/feed.xml"
    assert seen["timeout"] == 10
