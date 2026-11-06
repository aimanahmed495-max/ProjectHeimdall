"""Shared polling interface for live OSINT sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterator, List, Set


@dataclass(frozen=True)
class SourceItem:
    """One report yielded by a source adapter.

    Attributes:
        source_name: Heimdall ``osint_sources.source_name`` for the adapter.
        text: Report body passed to the keyword filter and classifier.
        timestamp: When the source published the report.
        external_id: Stable id used to deduplicate across polls.
    """

    source_name: str
    text: str
    timestamp: datetime
    external_id: str


class SourceAdapter(ABC):
    """Poll a public source and yield each external id at most once."""

    def __init__(self, source_name: str) -> None:
        """Remember ``source_name`` and the ids already returned.

        Args:
            source_name: Value stored in ``osint_sources.source_name``.
        """

        self._source_name = source_name
        self._seen_ids: Set[str] = set()

    @property
    def source_name(self) -> str:
        """Return the Heimdall source name for this adapter.

        Returns:
            The ``source_name`` passed to the constructor.
        """

        return self._source_name

    @abstractmethod
    def registration_payload(self) -> Dict[str, Any]:
        """Return an ``OsintSourceCreate`` body for this adapter.

        Returns:
            Dict with ``source_name``, ``source_type``, ``url``, and
            ``reliability_score``.
        """

    def poll(self) -> Iterator[SourceItem]:
        """Yield new items, skipping external ids already returned.

        Yields:
            :class:`SourceItem` values whose ``external_id`` has not been
            returned by a previous ``poll`` call.
        """

        for item in self._fetch_items():
            if not self._remember(item.external_id):
                continue
            yield item

    @abstractmethod
    def _fetch_items(self) -> List[SourceItem]:
        """Download the current page of items, including ones already seen."""

    def _remember(self, external_id: str) -> bool:
        """Return True when ``external_id`` has not been returned before."""

        if not external_id or external_id in self._seen_ids:
            return False
        self._seen_ids.add(external_id)
        return True
