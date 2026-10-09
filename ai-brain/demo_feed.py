"""Local RSS demo server for the Heimdall OSINT adapter.

Run from the repository root:

    python ai-brain/demo_feed.py

The server uses only the Python standard library. GET / is a small form,
POST /items stores a report in memory, and GET /feed.xml serves RSS 2.0.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import List, Sequence
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class DemoItem:
    """One report held by the demo feed."""

    guid: str
    title: str
    description: str
    published: datetime


class DemoFeedStore:
    """In-memory list of reports submitted to the demo server."""

    def __init__(self) -> None:
        """Start with an empty feed."""

        self._items: List[DemoItem] = []
        self._next_id = 1

    def add(self, text: str) -> DemoItem:
        """Append one report and return it.

        Args:
            text: Report body from the form.

        Returns:
            The stored item.
        """

        item = DemoItem(
            guid=f"demo-{self._next_id}",
            title="Demo report",
            description=text.strip(),
            published=datetime.now(timezone.utc),
        )
        self._items.append(item)
        self._next_id += 1
        return item

    def items(self) -> List[DemoItem]:
        """Return the reports posted so far, oldest first."""

        return list(self._items)


class DemoFeedServer(ThreadingHTTPServer):
    """HTTP server that shares one :class:`DemoFeedStore`."""

    allow_reuse_address = True

    def __init__(self, port: int, store: DemoFeedStore) -> None:
        """Listen on loopback for ``port`` and keep ``store``."""

        self.feed_store = store
        super().__init__(("127.0.0.1", port), DemoFeedHandler)


class DemoFeedHandler(BaseHTTPRequestHandler):
    """Serve the form, the RSS document, and the item submission route."""

    def do_GET(self) -> None:
        """Return the form or the RSS document."""

        path = urlparse(self.path).path
        if path == "/feed.xml":
            self._send_feed()
            return
        if path == "/":
            self._send_form()
            return
        self._send(404, "text/plain; charset=utf-8", b"Not found")

    def do_POST(self) -> None:
        """Store a form submission posted to ``/items``."""

        if urlparse(self.path).path != "/items":
            self._send(404, "text/plain; charset=utf-8", b"Not found")
            return
        self._accept_item()

    def _send_form(self) -> None:
        """Return the HTML form."""

        body = build_form_page().encode("utf-8")
        self._send(200, "text/html; charset=utf-8", body)

    def _send_feed(self) -> None:
        """Return RSS for the reports stored so far."""

        xml = build_rss(self._feed_store().items()).encode("utf-8")
        self._send(200, "application/rss+xml; charset=utf-8", xml)

    def _accept_item(self) -> None:
        """Add non-empty form text, then redirect back to the form."""

        text = text_from_form(read_request_body(self))
        if text:
            self._feed_store().add(text)
        self._redirect("/")

    def _feed_store(self) -> DemoFeedStore:
        """Return the store attached to this process's server."""

        store = getattr(self.server, "feed_store", None)
        if not isinstance(store, DemoFeedStore):
            raise RuntimeError("Demo feed store is not configured.")
        return store

    def _redirect(self, location: str) -> None:
        """Send the browser back to ``location``."""

        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        """Write one complete HTTP response."""

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_form_page() -> str:
    """Return the demo page with a text box and a Submit button."""

    return """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Heimdall demo feed</title></head>
<body>
<h1>Heimdall demo feed</h1>
<form method="post" action="/items">
<label for="text">Report</label>
<textarea id="text" name="text" rows="4" cols="60"></textarea>
<button type="submit">Submit</button>
</form>
<p><a href="/feed.xml">feed.xml</a></p>
</body>
</html>
"""


def build_rss(
    items: Sequence[DemoItem],
    link: str = "http://127.0.0.1:8001/",
) -> str:
    """Return an RSS 2.0 document for ``items``."""

    rendered = "".join(_rss_item(item) for item in items)
    safe_link = xml_escape(link)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        "    <title>Heimdall demo feed</title>\n"
        f"    <link>{safe_link}</link>\n"
        "    <description>Local demo reports for Heimdall OSINT.</description>\n"
        f"{rendered}"
        "  </channel>\n"
        "</rss>\n"
    )


def text_from_form(body: bytes) -> str:
    """Return the ``text`` field from an HTML form body."""

    parsed = parse_qs(body.decode("utf-8", errors="replace"))
    values = parsed.get("text", [])
    if not values:
        return ""
    return values[0].strip()


def read_request_body(handler: BaseHTTPRequestHandler) -> bytes:
    """Read the request body, capped so a huge post cannot fill memory."""

    length = _content_length(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return b""
    return handler.rfile.read(min(length, 8192))


def demo_port() -> int:
    """Return ``DEMO_FEED_PORT``, or 8001 when the value is unusable."""

    raw = os.getenv("DEMO_FEED_PORT", "8001")
    try:
        port = int(raw)
    except ValueError:
        return 8001
    if port < 1 or port > 65535:
        return 8001
    return port


def serve() -> None:
    """Listen until Ctrl+C."""

    port = demo_port()
    server = DemoFeedServer(port, DemoFeedStore())
    print(f"Demo RSS form at http://127.0.0.1:{port}/")
    print(f"Demo RSS feed at http://127.0.0.1:{port}/feed.xml")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def _rss_item(item: DemoItem) -> str:
    """Render one RSS item."""

    published = format_datetime(item.published, usegmt=True)
    return (
        "    <item>\n"
        f"      <title>{xml_escape(item.title)}</title>\n"
        f"      <description>{xml_escape(item.description)}</description>\n"
        f'      <guid isPermaLink="false">{xml_escape(item.guid)}</guid>\n'
        f"      <pubDate>{published}</pubDate>\n"
        "    </item>\n"
    )


def xml_escape(value: str) -> str:
    """Escape text for an XML element body."""

    return escape(value, quote=False)


def _content_length(raw: str) -> int:
    """Return a non-negative content length, or 0 when it is invalid."""

    try:
        length = int(raw)
    except ValueError:
        return 0
    if length < 0:
        return 0
    return length


def main() -> None:
    """Entrypoint used by ``python ai-brain/demo_feed.py``."""

    serve()


if __name__ == "__main__":
    main()
