"""Drop OSINT text that does not match the configured keywords."""

from __future__ import annotations

import logging
import os
from typing import Iterable, List, Tuple

from osint_logging import log_event
from source_adapter import SourceItem

logger = logging.getLogger(__name__)

DEFAULT_KEYWORDS: Tuple[str, ...] = (
    "shots",
    "gun",
    "weapon",
    "armed",
    "fire",
    "explosion",
    "suspicious",
    "fight",
    "robbery",
    "threat",
)


class KeywordFilter:
    """Case-insensitive substring filter applied before the LLM."""

    def __init__(self, keywords: Iterable[str]) -> None:
        """Store normalized keywords.

        Args:
            keywords: Words or phrases matched against report text.
        """

        self._keywords = self._normalize(keywords)

    @classmethod
    def from_env(cls) -> "KeywordFilter":
        """Read ``OSINT_KEYWORDS``, falling back to :data:`DEFAULT_KEYWORDS`.

        Returns:
            A filter built from the comma-separated env value, or the
            default keyword list when the env value is empty.
        """

        raw = os.getenv("OSINT_KEYWORDS", "")
        keywords = [part.strip() for part in raw.split(",") if part.strip()]
        if not keywords:
            return cls(DEFAULT_KEYWORDS)
        return cls(keywords)

    def matches(self, text: str) -> bool:
        """Return True when ``text`` contains any keyword, ignoring case.

        Args:
            text: Report body to scan.

        Returns:
            ``True`` when at least one configured keyword is a substring.
        """

        lowered = text.lower()
        return any(keyword in lowered for keyword in self._keywords)

    def keep(self, items: Iterable[SourceItem]) -> List[SourceItem]:
        """Return matching items and log the ones that are dropped.

        Args:
            items: Source items to filter before classification.

        Returns:
            Items whose text matched at least one keyword, in input order.
        """

        kept: List[SourceItem] = []
        for item in items:
            if self.matches(item.text):
                kept.append(item)
                continue
            self._log_drop(item)
        return kept

    def _log_drop(self, item: SourceItem) -> None:
        """Record that an item never reached the classifier."""

        log_event(
            logger,
            logging.INFO,
            "keyword_drop",
            f"Dropped OSINT item {item.external_id} from {item.source_name}: "
            "no keyword match.",
            external_id=item.external_id,
            source=item.source_name,
        )

    @staticmethod
    def _normalize(keywords: Iterable[str]) -> Tuple[str, ...]:
        """Trim and lowercase keywords, skipping blanks."""

        normalized = (keyword.strip().lower() for keyword in keywords if keyword)
        return tuple(keyword for keyword in normalized if keyword)
