"""HTTP client for the Heimdall Core API."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class HeimdallAPIError(Exception):
    """Raised when the Heimdall Core API returns an unexpected response."""


class HeimdallAPIUnavailableError(HeimdallAPIError):
    """Raised when the Heimdall Core API cannot be reached."""


class HeimdallAPIClient:
    """Thin wrapper around REST calls to the Heimdall Core API.

    The client reads ``BASE_URL`` from the environment and defaults to
    ``http://localhost:8000``. Connection failures are converted into
    :class:`HeimdallAPIUnavailableError` so callers can fail gracefully
    when the backend is not running.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        """Create a client pointed at the Heimdall Core API.

        Args:
            base_url: API origin. When omitted, ``BASE_URL`` is read from
                the environment, falling back to ``http://localhost:8000``.
            timeout: Per-request timeout in seconds.
        """

        resolved = base_url or os.getenv("BASE_URL", "http://localhost:8000")
        self._base_url = resolved.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    @property
    def base_url(self) -> str:
        """Return the API origin this client is using."""

        return self._base_url

    def register_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Register an OSINT source with ``POST /sources``.

        A ``409 Conflict`` is treated as success when the source name is
        already stored. In that case the existing record is returned when
        it can be found, and ``already_registered`` is set to ``True``.

        Args:
            source: Payload matching ``OsintSourceCreate``
                (``source_name``, ``source_type``, ``url``,
                ``reliability_score``).

        Returns:
            The created or existing source record, plus
            ``already_registered``.

        Raises:
            HeimdallAPIUnavailableError: The API is not reachable.
            HeimdallAPIError: The API returned an unexpected status.
        """

        response = self._request("POST", "/sources", json_body=source)

        if response.status_code == 409:
            existing = self._find_source_by_name(source.get("source_name", ""))
            result = dict(existing or source)
            result["already_registered"] = True
            return result

        self._ensure_success(response, expected_status=201)
        payload = response.json()
        payload["already_registered"] = False
        return payload

    def post_threat_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Create a threat event with ``POST /threat-events``.

        Args:
            event: Payload matching ``ThreatEventCreate``
                (``object_class``, ``confidence_score``, ``camera_id``,
                optional ``status``).

        Returns:
            The created threat-event record from the API.

        Raises:
            HeimdallAPIUnavailableError: The API is not reachable.
            HeimdallAPIError: The API returned an unexpected status.
        """

        response = self._request("POST", "/threat-events", json_body=event)
        self._ensure_success(response, expected_status=201)
        return response.json()

    def post_system_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Create a system log with ``POST /system-logs``.

        Args:
            log_entry: Payload matching ``SystemLogCreate``
                (``module``, ``message``, optional ``event_id``).

        Returns:
            The created system-log record from the API.

        Raises:
            HeimdallAPIUnavailableError: The API is not reachable.
            HeimdallAPIError: The API returned an unexpected status.
        """

        response = self._request("POST", "/system-logs", json_body=log_entry)
        self._ensure_success(response, expected_status=201)
        return response.json()

    def _find_source_by_name(self, source_name: str) -> Optional[Dict[str, Any]]:
        """Return a previously registered source with the given name."""

        if not source_name:
            return None

        try:
            response = self._request("GET", "/sources")
        except HeimdallAPIError:
            return None

        if response.status_code != 200:
            return None

        try:
            sources = response.json()
        except ValueError:
            return None

        if not isinstance(sources, list):
            return None

        for source in sources:
            if (
                isinstance(source, dict)
                and source.get("source_name") == source_name
            ):
                return source

        return None

    def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Send an HTTP request and translate connection failures."""

        url = f"{self._base_url}{path}"

        try:
            return self._session.request(
                method,
                url,
                json=json_body,
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise HeimdallAPIUnavailableError(
                f"Heimdall API is not reachable at {self._base_url}. "
                "Start the backend first (see backend/README.md), then "
                "rerun this module."
            ) from exc

    def _ensure_success(
        self,
        response: requests.Response,
        expected_status: int,
    ) -> None:
        """Raise ``HeimdallAPIError`` when the status code is unexpected."""

        if response.status_code == expected_status:
            return

        detail: Any = response.text
        try:
            payload = response.json()
            detail = payload.get("detail", payload)
        except ValueError:
            pass

        raise HeimdallAPIError(
            f"{response.request.method} {response.url} failed "
            f"({response.status_code}): {detail}"
        )
