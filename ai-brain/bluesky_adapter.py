"""Poll a short Bluesky account watchlist via getAuthorFeed."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence
from urllib.parse import urlencode

import requests
from osint_logging import log_event
from source_adapter import SourceAdapter, SourceItem

logger = logging.getLogger(__name__)

NO_UNAUTHENTICATED = "!no-unauthenticated"
POST_TYPE = "app.bsky.feed.post"
AUTHOR_FEED_PATH = "/xrpc/app.bsky.feed.getAuthorFeed"


class BlueskyAdapter(SourceAdapter):
    """Poll ``app.bsky.feed.getAuthorFeed`` for each configured actor.

    Unauthenticated AppView GETs only. Keyword search is not used. Each
    watched account shares one Heimdall ``source_name``, so two Bluesky
    accounts never corroborate each other.
    """

    SOURCE_NAME = "bluesky-watchlist"
    DEFAULT_APPVIEW = "https://public.api.bsky.app"
    PAGE_LIMIT = 25
    MAX_ACTORS = 10
    MAX_AGE = timedelta(minutes=10)

    def __init__(
        self,
        appview: str,
        actors: Sequence[str],
        timeout: float = 10.0,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Point the adapter at one AppView and a short actor list.

        Args:
            appview: Bluesky AppView origin such as
                ``https://public.api.bsky.app``.
            actors: Handles or DIDs to poll. At most ``MAX_ACTORS``.
            timeout: Per-request timeout in seconds.
            clock: Returns "now" for the startup age window. Defaults to
                UTC ``datetime.now``.

        Raises:
            ValueError: ``actors`` is empty or longer than ``MAX_ACTORS``.
        """

        super().__init__(self.SOURCE_NAME)
        cleaned = [actor.strip() for actor in actors if actor and actor.strip()]
        if not cleaned:
            raise ValueError("BLUESKY_ACTORS is not set.")
        if len(cleaned) > self.MAX_ACTORS:
            raise ValueError(
                f"BLUESKY_ACTORS has more than {self.MAX_ACTORS} accounts."
            )
        self._appview = appview.strip().rstrip("/") or self.DEFAULT_APPVIEW
        self._actors = cleaned
        self._timeout = timeout
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @classmethod
    def from_env(cls) -> "BlueskyAdapter":
        """Build an adapter from ``BLUESKY_APPVIEW_URL`` and ``BLUESKY_ACTORS``.

        Returns:
            An adapter pointed at the configured AppView and actors.

        Raises:
            ValueError: ``BLUESKY_ACTORS`` is missing, blank, or too long.
        """

        appview = os.getenv("BLUESKY_APPVIEW_URL", cls.DEFAULT_APPVIEW)
        raw_actors = os.getenv("BLUESKY_ACTORS", "")
        actors = [part.strip() for part in raw_actors.split(",")]
        return cls(appview=appview, actors=actors)

    def registration_payload(self) -> Dict[str, Any]:
        """Return the ``POST /sources`` body for the Bluesky watchlist.

        Returns:
            An ``OsintSourceCreate`` dict for the getAuthorFeed path.
        """

        return {
            "source_name": self.SOURCE_NAME,
            "source_type": "Social Media",
            "url": f"{self._appview}{AUTHOR_FEED_PATH}",
            "reliability_score": 0.5,
        }

    def _fetch_items(self) -> List[SourceItem]:
        """GET one page per actor and merge the accepted posts."""

        items: List[SourceItem] = []
        last_error: Optional[requests.RequestException] = None
        successes = 0
        for actor in self._actors:
            try:
                items.extend(self._fetch_actor(actor))
                successes += 1
            except requests.RequestException as exc:
                last_error = exc
                self._warn_actor_failure(actor, exc)
        if successes == 0 and last_error is not None:
            raise last_error
        return items

    def _fetch_actor(self, actor: str) -> List[SourceItem]:
        """GET one actor's author feed and parse accepted posts.

        Args:
            actor: Handle or DID.

        Returns:
            Source items for that actor's page. Invalid JSON yields none.

        Raises:
            requests.RequestException: The GET failed or returned an error.
        """

        response = requests.get(
            self._author_feed_url(actor),
            timeout=self._timeout,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError:
            return []
        return self._parse_feed(payload)
    def _author_feed_url(self, actor: str) -> str:
        """Return the unauthenticated getAuthorFeed URL for one actor."""

        query = urlencode(
            (
                ("actor", actor),
                ("limit", str(self.PAGE_LIMIT)),
                ("filter", "posts_no_replies"),
            )
        )
        return f"{self._appview}{AUTHOR_FEED_PATH}?{query}"

    def _warn_actor_failure(
        self,
        actor: str,
        exc: requests.RequestException,
    ) -> None:
        """Log one actor failure without the response body."""

        status = None
        response = getattr(exc, "response", None)
        if response is not None:
            status = getattr(response, "status_code", None)
        detail = f"status={status}" if status is not None else type(exc).__name__
        log_event(
            logger,
            logging.WARNING,
            "bluesky_actor_error",
            f"Bluesky actor poll failed for {actor} ({detail})",
            actor=actor,
            status_code=status,
            error_type=type(exc).__name__,
        )
    def _parse_feed(self, payload: Any) -> List[SourceItem]:
        """Parse a getAuthorFeed JSON body into source items."""

        if not isinstance(payload, dict):
            return []
        feed = payload.get("feed")
        if not isinstance(feed, list):
            return []
        items: List[SourceItem] = []
        for entry in feed:
            item = self._parse_entry(entry)
            if item is not None:
                items.append(item)
        return items

    def _parse_entry(self, entry: Any) -> Optional[SourceItem]:
        """Return a source item when the feed entry is an accepted post."""

        if not isinstance(entry, dict) or entry.get("reason"):
            return None
        post = entry.get("post")
        if not isinstance(post, dict):
            return None
        if self._has_no_unauthenticated(post.get("author")):
            return None
        uri = post.get("uri")
        if not isinstance(uri, str) or not uri.startswith("at://"):
            return None
        record = post.get("record")
        if not isinstance(record, dict) or record.get("$type") != POST_TYPE:
            return None
        text = record.get("text")
        if not isinstance(text, str) or not text.strip():
            return None
        timestamp = self._indexed_at(post.get("indexedAt"))
        if self._too_old(timestamp):
            return None
        return SourceItem(
            source_name=self.source_name,
            text=text.strip(),
            timestamp=timestamp,
            external_id=uri,
        )

    def _has_no_unauthenticated(self, author: Any) -> bool:
        """Return True when the author carries ``!no-unauthenticated``."""

        if not isinstance(author, dict):
            return False
        labels = author.get("labels")
        if not isinstance(labels, list):
            return False
        for label in labels:
            if isinstance(label, dict) and label.get("val") == NO_UNAUTHENTICATED:
                return True
        return False

    def _indexed_at(self, raw: Any) -> datetime:
        """Parse AppView ``indexedAt``, or fall back to the clock."""

        if isinstance(raw, str) and raw.strip():
            try:
                parsed = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
            except ValueError:
                return self._clock()
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        return self._clock()

    def _too_old(self, timestamp: datetime) -> bool:
        """Return True when ``timestamp`` is older than ``MAX_AGE``."""

        now = self._clock()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return timestamp < now - self.MAX_AGE
