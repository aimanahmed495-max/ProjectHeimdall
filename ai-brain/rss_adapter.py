"""Poll a public RSS 2.0 feed with the standard-library XML parser."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import requests
from source_adapter import SourceAdapter, SourceItem


class RssAdapter(SourceAdapter):
    """Fetch ``RSS_FEED_URL`` and yield one item per RSS ``guid``."""

    SOURCE_NAME = "local-rss-feed"
    DEFAULT_FEED_URL = "http://localhost:8001/feed.xml"

    def __init__(self, feed_url: str, timeout: float = 10.0) -> None:
        """Point the adapter at one RSS document.

        Args:
            feed_url: Absolute URL of an RSS 2.0 document.
            timeout: Per-request timeout in seconds.
        """

        super().__init__(self.SOURCE_NAME)
        self._feed_url = feed_url.strip() or self.DEFAULT_FEED_URL
        self._timeout = timeout

    @classmethod
    def from_env(cls) -> "RssAdapter":
        """Build an adapter from ``RSS_FEED_URL``."""

        feed_url = os.getenv("RSS_FEED_URL", cls.DEFAULT_FEED_URL)
        return cls(feed_url=feed_url)

    def registration_payload(self) -> Dict[str, Any]:
        """Return the ``POST /sources`` body for the local RSS feed."""

        return {
            "source_name": self.SOURCE_NAME,
            "source_type": "RSS",
            "url": self._feed_url,
            "reliability_score": 0.5,
        }

    def _fetch_items(self) -> List[SourceItem]:
        """GET the feed and return its items."""

        response = requests.get(self._feed_url, timeout=self._timeout)
        response.raise_for_status()
        return self._parse_feed(response.text)

    def _parse_feed(self, xml_text: str) -> List[SourceItem]:
        """Parse an RSS document. Invalid XML yields no items."""

        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError:
            return []
        channel = self._find_child(root, "channel")
        if channel is None:
            return []
        return self._parse_channel(channel)

    def _parse_channel(self, channel: ElementTree.Element) -> List[SourceItem]:
        """Convert channel ``item`` nodes into source items."""

        items: List[SourceItem] = []
        for node in list(channel):
            if not self._tag_is(node, "item"):
                continue
            item = self._parse_item(node)
            if item is not None:
                items.append(item)
        return items

    def _parse_item(self, node: ElementTree.Element) -> Optional[SourceItem]:
        """Return an item when it has both a guid and some text."""

        external_id = self._child_text(node, "guid")
        text = self._item_text(node)
        if not external_id or not text:
            return None
        return SourceItem(
            source_name=self.source_name,
            text=text,
            timestamp=self._published_at(node),
            external_id=external_id,
        )

    def _item_text(self, node: ElementTree.Element) -> str:
        """Join the item title and description into classifier text."""

        title = self._child_text(node, "title")
        description = self._child_text(node, "description")
        parts = [part for part in (title, description) if part]
        return "\n".join(parts).strip()

    def _published_at(self, node: ElementTree.Element) -> datetime:
        """Parse RFC 822 ``pubDate``, or use the current time."""

        raw = self._child_text(node, "pubDate")
        parsed = self._parse_pub_date(raw)
        if parsed is None:
            return datetime.now(timezone.utc)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _parse_pub_date(self, raw: str) -> Optional[datetime]:
        """Return a datetime for an RSS publication date, or None."""

        if not raw:
            return None
        try:
            return parsedate_to_datetime(raw)
        except (TypeError, ValueError, IndexError):
            return None

    def _find_child(
        self,
        node: ElementTree.Element,
        name: str,
    ) -> Optional[ElementTree.Element]:
        """Return the first child element with this local name."""

        for child in list(node):
            if self._tag_is(child, name):
                return child
        return None

    def _child_text(self, node: ElementTree.Element, name: str) -> str:
        """Return stripped text for the first matching child."""

        child = self._find_child(node, name)
        if child is None or child.text is None:
            return ""
        return child.text.strip()

    @staticmethod
    def _tag_is(node: ElementTree.Element, name: str) -> bool:
        """Match a tag with or without an XML namespace."""

        tag = node.tag
        if not isinstance(tag, str):
            return False
        return tag == name or tag.endswith("}" + name)
