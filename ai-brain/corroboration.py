"""Decide when independent OSINT reports corroborate one category."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Corroboration:
    """A category reported by two or more sources inside the window."""

    category: str
    event_ids: Tuple[int, ...]
    source_ids: Tuple[int, ...]


@dataclass(frozen=True)
class _Sighting:
    """One classified report kept for the sliding window."""

    source_id: int
    event_id: int
    reported_at: datetime


class CorroborationTracker:
    """Fire once when distinct sources agree on a threat category.

    The category is the ``object_class`` already returned by
    :class:`osint_agent.OsintAgent`. Two reports that share a source id
    never count as corroboration.
    """

    def __init__(self, window_seconds: int = 300) -> None:
        """Remember reports for ``window_seconds``.

        Args:
            window_seconds: Maximum age of a report that can still count.
        """

        self._window = timedelta(seconds=window_seconds)
        self._sightings: Dict[str, List[_Sighting]] = {}
        self._fired: set[str] = set()

    def observe(
        self,
        source_id: int,
        category: str,
        event_id: int,
        reported_at: datetime,
    ) -> Optional[Corroboration]:
        """Record one report and maybe return a new corroboration.

        Args:
            source_id: Heimdall source that produced the threat event.
            category: Agent ``object_class`` for that event.
            event_id: Threat event to patch if this category corroborates.
            reported_at: When the source item was published.

        Returns:
            The corroboration the first time two distinct sources agree,
            otherwise ``None``.
        """

        key = category.strip().lower()
        if not key or key in self._fired:
            return None
        moment = self._as_utc(reported_at)
        self._prune(key, moment)
        self._store(key, source_id, event_id, moment)
        if len(self._distinct_sources(key)) < 2:
            return None
        self._fired.add(key)
        return self._build(key)

    def release(self, category: str) -> None:
        """Allow ``category`` to fire again after a failed activation."""

        self._fired.discard(category.strip().lower())

    def _store(
        self,
        key: str,
        source_id: int,
        event_id: int,
        moment: datetime,
    ) -> None:
        """Append one sighting for ``key``."""

        sighting = _Sighting(source_id, event_id, moment)
        self._sightings.setdefault(key, []).append(sighting)

    def _prune(self, key: str, moment: datetime) -> None:
        """Drop sightings older than the window relative to ``moment``."""

        cutoff = moment - self._window
        kept = [
            sighting
            for sighting in self._sightings.get(key, [])
            if sighting.reported_at >= cutoff
        ]
        self._sightings[key] = kept

    def _distinct_sources(self, key: str) -> List[int]:
        """Return source ids in the order they were first seen."""

        sources: List[int] = []
        for sighting in self._sightings.get(key, []):
            if sighting.source_id not in sources:
                sources.append(sighting.source_id)
        return sources

    def _build(self, key: str) -> Corroboration:
        """Collect the event ids currently inside the window."""

        event_ids: List[int] = []
        for sighting in self._sightings.get(key, []):
            if sighting.event_id not in event_ids:
                event_ids.append(sighting.event_id)
        return Corroboration(
            category=key,
            event_ids=tuple(event_ids),
            source_ids=tuple(self._distinct_sources(key)),
        )

    @staticmethod
    def _as_utc(moment: datetime) -> datetime:
        """Return an aware UTC timestamp."""

        if moment.tzinfo is None:
            return moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc)
