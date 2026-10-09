"""Poll live adapters, classify matches, and corroborate categories."""

from __future__ import annotations

import sys
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence

import requests
from camera_activation import CameraActivator
from corroboration import Corroboration, CorroborationTracker
from keyword_filter import KeywordFilter
from ntfy_adapter import NtfyAdapter
from osint_client import HeimdallAPIClient, HeimdallAPIError
from osint_settings import camera_id, corroboration_window_seconds, poll_seconds
from rss_adapter import RssAdapter
from source_adapter import SourceAdapter, SourceItem


class AlertAgent(Protocol):
    """The subset of ``OsintAgent`` the live loop needs."""

    def run(self, alert_text: str, source_id: int) -> Dict[str, Any]:
        """Classify one alert and post its threat event."""


class LiveOsintRunner:
    """Register live sources and poll them until stopped."""

    def __init__(
        self,
        client: HeimdallAPIClient,
        agent: AlertAgent,
        adapters: Optional[Sequence[SourceAdapter]] = None,
        keyword_filter: Optional[KeywordFilter] = None,
        tracker: Optional[CorroborationTracker] = None,
        activator: Optional[CameraActivator] = None,
        poll_interval: Optional[float] = None,
        sleep: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Wire the live loop.

        Args:
            client: Authenticated Heimdall API client.
            agent: Classifier. Tests inject a fake so Groq is not constructed.
            adapters: Sources to poll. Defaults to ntfy and the local RSS feed.
            keyword_filter: Pre-LLM filter. Defaults to ``OSINT_KEYWORDS``.
            tracker: Corroboration state. Defaults to the configured window.
            activator: Publishes corroboration to the API.
            poll_interval: Seconds between polls. Defaults to
                ``OSINT_POLL_SECONDS``.
            sleep: Wait function, replaced in tests.
        """

        self._client = client
        self._agent = agent
        self._adapters = self._select_adapters(adapters)
        self._keywords = keyword_filter or KeywordFilter.from_env()
        self._tracker = tracker or CorroborationTracker(
            window_seconds=corroboration_window_seconds(),
        )
        self._activator = activator or CameraActivator(
            client,
            camera_id=camera_id(),
        )
        self._poll_interval = poll_seconds() if poll_interval is None else poll_interval
        self._sleep = sleep or self._default_sleep

    def register_sources(self) -> Dict[str, int]:
        """Fetch existing sources, create any that are missing, and map ids.

        Returns:
            Mapping of adapter source name to ``source_id``.

        Raises:
            HeimdallAPIError: The sources API failed.
            ValueError: A created source did not return ``source_id``.
        """

        existing = self._existing_ids()
        mapping: Dict[str, int] = {}
        for adapter in self._adapters:
            mapping[adapter.source_name] = self._id_for(adapter, existing)
        return mapping

    def run(self, max_cycles: Optional[int] = None) -> int:
        """Poll until interrupted, or until ``max_cycles`` when set.

        Args:
            max_cycles: Stop after this many polls. ``None`` polls forever.

        Returns:
            Process exit code. Keyboard interrupt returns 0.
        """

        source_ids = self.register_sources()
        self._print_source_ids(source_ids)
        try:
            return self._poll_loop(source_ids, max_cycles)
        except KeyboardInterrupt:
            print("\nStopped live OSINT polling.")
            return 0

    def _select_adapters(
        self,
        adapters: Optional[Sequence[SourceAdapter]],
    ) -> List[SourceAdapter]:
        """Use the injected adapters, or the ntfy and RSS defaults."""

        if adapters is not None:
            return list(adapters)
        return [NtfyAdapter.from_env(), RssAdapter.from_env()]

    def _existing_ids(self) -> Dict[str, int]:
        """Map source names already stored by the API."""

        found: Dict[str, int] = {}
        for row in self._client.list_sources():
            self._remember_existing(found, row)
        return found

    def _remember_existing(self, found: Dict[str, int], row: Dict[str, Any]) -> None:
        """Copy one source row into ``found`` when it has a name and id."""

        name = row.get("source_name")
        source_id = row.get("source_id")
        if isinstance(name, str) and isinstance(source_id, int):
            found[name] = source_id

    def _id_for(self, adapter: SourceAdapter, existing: Dict[str, int]) -> int:
        """Reuse a stored source id, or register the adapter."""

        if adapter.source_name in existing:
            return existing[adapter.source_name]
        created = self._client.register_source(adapter.registration_payload())
        source_id = created.get("source_id")
        if not isinstance(source_id, int):
            raise ValueError(
                f"Registered source {adapter.source_name} has no source_id."
            )
        return source_id

    def _print_source_ids(self, source_ids: Dict[str, int]) -> None:
        """Print the source id chosen for each adapter."""

        print("Live sources:")
        for name, source_id in source_ids.items():
            print(f"  {name} (id={source_id})")
        print()

    def _poll_loop(
        self,
        source_ids: Dict[str, int],
        max_cycles: Optional[int],
    ) -> int:
        """Poll, then sleep, until the cycle limit is reached."""

        completed = 0
        while True:
            self._run_cycle(source_ids)
            completed += 1
            if self._finished(completed, max_cycles):
                return 0
            self._sleep(self._poll_interval)

    def _finished(self, completed: int, max_cycles: Optional[int]) -> bool:
        """Return True when a finite run has completed its polls."""

        return max_cycles is not None and completed >= max_cycles

    def _run_cycle(self, source_ids: Dict[str, int]) -> None:
        """Poll every adapter once."""

        for adapter in self._adapters:
            self._process_adapter(adapter, source_ids)

    def _process_adapter(
        self,
        adapter: SourceAdapter,
        source_ids: Dict[str, int],
    ) -> None:
        """Filter and classify one adapter's new items."""

        source_id = source_ids.get(adapter.source_name)
        if source_id is None:
            return
        for item in self._new_items(adapter):
            self._process_item(item, source_id)

    def _new_items(self, adapter: SourceAdapter) -> List[SourceItem]:
        """Poll one adapter and drop text that fails the keyword filter."""

        try:
            fetched = list(adapter.poll())
        except requests.RequestException as exc:
            self._report_error(exc)
            return []
        return self._keywords.keep(fetched)

    def _process_item(self, item: SourceItem, source_id: int) -> None:
        """Run the agent, then update corroboration for one item."""

        try:
            result = self._agent.run(item.text, source_id)
        except HeimdallAPIError as exc:
            self._report_error(exc)
            return
        if not isinstance(result, dict):
            return
        self._announce(item, result)
        self._consider(result, source_id, item.timestamp)

    def _announce(self, item: SourceItem, result: Dict[str, Any]) -> None:
        """Print the classification outcome for one live item."""

        label = result.get("object_class") or result.get("error") or "not classified"
        print(f"Live item {item.external_id}: {label}")

    def _consider(
        self,
        result: Dict[str, Any],
        source_id: int,
        reported_at: datetime,
    ) -> None:
        """Feed one agent result to the tracker and activate on a new hit."""

        if result.get("error"):
            return
        category = self._category(result)
        event_id = self._event_id(result)
        if category is None or event_id is None:
            return
        outcome = self._tracker.observe(source_id, category, event_id, reported_at)
        if outcome is None:
            return
        self._activate(outcome)

    def _activate(self, outcome: Corroboration) -> None:
        """Publish a corroboration, releasing it if the API call fails."""

        try:
            self._activator.activate(outcome)
        except HeimdallAPIError as exc:
            self._tracker.release(outcome.category)
            self._report_error(exc)

    def _category(self, result: Dict[str, Any]) -> Optional[str]:
        """Return the agent object class when it is a non-empty string."""

        category = result.get("object_class")
        if isinstance(category, str) and category.strip():
            return category
        return None

    def _event_id(self, result: Dict[str, Any]) -> Optional[int]:
        """Return the posted threat-event id, when the agent stored one."""

        threat = result.get("threat_event")
        if not isinstance(threat, dict):
            return None
        event_id = threat.get("event_id")
        if isinstance(event_id, int) and event_id > 0:
            return event_id
        return None

    def _report_error(self, exc: Exception) -> None:
        """Print a controlled live-loop error and keep polling."""

        print(f"Error: {exc}", file=sys.stderr)

    @staticmethod
    def _default_sleep(seconds: float) -> None:
        """Wait between polls."""

        time.sleep(seconds)
