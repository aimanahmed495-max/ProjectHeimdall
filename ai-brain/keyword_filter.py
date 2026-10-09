"""Drop OSINT text that does not match the configured keywords."""

from __future__ import annotations

import logging
import os
from typing import Iterable, List, Tuple

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
        """Read ``OSINT_KEYWORDS``, falling back to :data:`DEFAULT_KEYWORDS`."""

        raw = os.getenv("OSINT_KEYWORDS", "")
        keywords = [part.strip() for part in raw.split(",") if part.strip()]
        if not keywords:
            return cls(DEFAULT_KEYWORDS)
        return cls(keywords)

    def matches(self, text: str) -> bool:
        """Return True when ``text`` contains any keyword, ignoring case."""

        lowered = text.lower()
        return any(keyword in lowered for keyword in self._keywords)

    def keep(self, items: Iterable[SourceItem]) -> List[SourceItem]:
        """Return matching items and log the ones that are dropped."""

        kept: List[SourceItem] = []
        for item in items:
            if self.matches(item.text):
                kept.append(item)
                continue
            self._log_drop(item)
        return kept

    def _log_drop(self, item: SourceItem) -> None:
        """Record that an item never reached the classifier."""

        logger.info(
            "Dropped OSINT item %s from %s: no keyword match.",
            item.external_id,
            item.source_name,
        )

    @staticmethod
    def _normalize(keywords: Iterable[str]) -> Tuple[str, ...]:
        """Trim and lowercase keywords, skipping blanks."""

        normalized = (keyword.strip().lower() for keyword in keywords if keyword)
        return tuple(keyword for keyword in normalized if keyword)
