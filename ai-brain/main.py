"""Run mock OSINT ingestion against the Heimdall Core API."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from osint_agent import OsintAgent, OsintAgentError, OsintAgentState
from osint_client import (
    HeimdallAPIClient,
    HeimdallAPIError,
    HeimdallAPIUnavailableError,
)


PACKAGE_DIR = Path(__file__).resolve().parent


class OsintIngestionApp:
    """Load mock OSINT data, register sources, and process alerts."""

    def __init__(self, package_dir: Path = PACKAGE_DIR) -> None:
        """Configure paths and load ``ai-brain/.env`` if present.

        Args:
            package_dir: Directory that contains the mock JSON files and
                optional ``.env``.
        """

        self._package_dir = package_dir
        load_dotenv(self._package_dir / ".env")
        self._client = HeimdallAPIClient()

    def run(self) -> int:
        """Register mock sources, process mock alerts, and print a summary.

        Returns:
            Process exit code: ``0`` on success, ``1`` on a controlled
            failure such as a missing API or Groq key.
        """

        print("Heimdall OSINT ingestion")
        print(f"API: {self._client.base_url}")
        print()

        try:
            sources = self._load_json_list("mock_sources.json")
            alerts = self._load_alerts("mock_alerts.json")
        except (OSError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        try:
            registered = self._register_sources(sources)
        except HeimdallAPIUnavailableError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        except HeimdallAPIError as exc:
            print(f"Error registering OSINT sources: {exc}", file=sys.stderr)
            return 1

        self._print_source_summary(registered)
        print()

        try:
            agent = OsintAgent(client=self._client)
        except OsintAgentError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        print(f"Processing {len(alerts)} mock alert(s)...\n")
        results = [agent.run(alert) for alert in alerts]
        self._print_alert_summary(results)

        posted = sum(
            1 for result in results if result.get("threat_event")
        )
        failed = sum(1 for result in results if result.get("error"))
        print()
        print(
            f"Done. Posted {posted}/{len(alerts)} threat event(s) "
            f"to {self._client.base_url}."
        )
        if failed:
            print(f"{failed} alert(s) finished with errors.")
            return 1

        return 0

    def _register_sources(
        self,
        sources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Register each mock source, tolerating names that already exist."""

        registered: List[Dict[str, Any]] = []
        for source in sources:
            registered.append(self._client.register_source(source))
        return registered

    def _load_json_list(self, filename: str) -> List[Dict[str, Any]]:
        """Load a JSON array of objects from the package directory."""

        path = self._package_dir / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{filename} must contain a JSON array.")
        return data

    def _load_alerts(self, filename: str) -> List[str]:
        """Load raw alert strings from ``mock_alerts.json``."""

        path = self._package_dir / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{filename} must contain a JSON array of strings.")

        alerts: List[str] = []
        for item in data:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    f"{filename} must contain non-empty alert strings."
                )
            alerts.append(item.strip())

        if not alerts:
            raise ValueError(f"{filename} does not contain any alerts.")

        return alerts

    def _print_source_summary(self, sources: List[Dict[str, Any]]) -> None:
        """Print how each mock source was registered."""

        print("Registered sources:")
        for source in sources:
            label = (
                "exists"
                if source.get("already_registered")
                else "created"
            )
            source_id = source.get("source_id", "-")
            name = source.get("source_name", "unknown")
            print(f"  [{label}] {name} (id={source_id})")

    def _print_alert_summary(self, results: List[OsintAgentState]) -> None:
        """Print alert → classification → API response for the live demo."""

        for index, result in enumerate(results, start=1):
            alert = result.get("alert_text", "")
            print(f"{index}. Alert: {alert}")

            error = result.get("error")
            object_class = result.get("object_class")
            if object_class:
                confidence = float(result.get("confidence_score", 0.0))
                print(
                    f"   Classification: {object_class} "
                    f"(confidence {confidence:.2f})"
                )
            elif error:
                print("   Classification: (failed)")

            threat_event = result.get("threat_event")
            if threat_event:
                print(
                    "   Threat event: "
                    f"id={threat_event.get('event_id')} "
                    f"status={threat_event.get('status')}"
                )
            else:
                print("   Threat event: (not posted)")

            system_log = result.get("system_log")
            if system_log:
                print(f"   System log: id={system_log.get('log_id')}")
            else:
                print("   System log: (not posted)")

            if error:
                print(f"   Error: {error}")

            print()


def main() -> int:
    """Entrypoint used by ``python main.py``."""

    return OsintIngestionApp().run()


if __name__ == "__main__":
    sys.exit(main())
