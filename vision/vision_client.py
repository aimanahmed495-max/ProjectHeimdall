"""HTTP client for the Heimdall Core API."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class HeimdallAPIError(Exception):
    """Raised when the Heimdall Core API returns an unexpected response."""


class HeimdallAPIUnavailableError(HeimdallAPIError):
    """Raised when the Heimdall Core API cannot be reached."""


class HeimdallVisionClient:
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
        username: Optional[str] = None,
        password: Optional[str] = None,
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
        self._username = username or os.getenv("VISION_API_USERNAME")
        self._password = password or os.getenv("VISION_API_PASSWORD")
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

    def authenticate(self) -> None:
        """Log in and attach a bearer token to future API requests."""

        if not self._username or not self._password:
            raise HeimdallAPIError(
                "Vision API credentials are missing. Set "
                "VISION_API_USERNAME and VISION_API_PASSWORD."
            )

        response = self._request(
            "POST",
            "/auth/login",
            json_body={
                "username": self._username,
                "password": self._password,
            },
        )
        self._ensure_success(response, expected_status=200)

        token = response.json().get("access_token")
        if not token:
            raise HeimdallAPIError(
                "Heimdall authentication response did not include an access token."
            )

        self._session.headers.update({"Authorization": f"Bearer {token}"})

    def post_camera_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a camera-state record with ``POST /camera-states``.

        Args:
            state: Payload matching ``CameraStateCreate``
                (``camera_id``, ``mode``, ``fps``, ``resolution``).
                ``mode`` must be ``Dormant`` or ``Active``.

        Returns:
            The created camera-state record from the API.

        Raises:
            HeimdallAPIUnavailableError: The API is not reachable.
            HeimdallAPIError: The API returned an unexpected status.
        """

        response = self._request("POST", "/camera-states", json_body=state)
        self._ensure_success(response, expected_status=201)
        return response.json()

    def set_camera_state(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Register a camera or update its existing state."""

        camera_id = state["camera_id"]
        path = f"/camera-states/{camera_id}"

        lookup_response = self._request("GET", path)

        if lookup_response.status_code == 404:
            return self.post_camera_state(state)

        self._ensure_success(
            lookup_response,
            expected_status=200,
        )

        update_payload = {
            "mode": state["mode"],
            "fps": state["fps"],
            "resolution": state["resolution"],
        }

        update_response = self._request(
            "PUT",
            path,
            json_body=update_payload,
        )
        self._ensure_success(
            update_response,
            expected_status=200,
        )

        return update_response.json()

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
