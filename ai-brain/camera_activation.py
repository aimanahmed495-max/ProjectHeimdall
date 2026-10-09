"""Turn a corroboration into Heimdall threat, camera, and log updates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Protocol

from corroboration import Corroboration


class ThreatApi(Protocol):
    """Client methods used to publish a corroboration."""

    def patch_threat_event(
        self,
        event_id: int,
        update: Dict[str, Any],
    ) -> Dict[str, Any]:
        """PATCH one threat event."""

    def put_camera_state(
        self,
        camera_id: int,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """PUT one camera state."""

    def post_system_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """POST one system log."""


class CameraActivator:
    """Patch corroborated events, set the camera Active, and write a log.

    ``PUT /camera-states/{camera_id}`` updates an existing camera. The
    camera row must already exist; this class does not create one.
    """

    CORROBORATED_STATUS = "Corroborated"
    MODULE_NAME = "osint-agent"
    DEFAULT_FPS = 5
    DEFAULT_RESOLUTION = "720p"

    def __init__(
        self,
        client: ThreatApi,
        camera_id: int = 1,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Bind the Heimdall client and the camera to activate.

        Args:
            client: API client that can patch events, put camera state,
                and post system logs.
            camera_id: ``camera_states.camera_id`` to set Active.
            clock: Supplies ``corroborated_at``. Defaults to UTC now.
        """

        self._client = client
        self._camera_id = camera_id
        self._clock = clock or self._now

    def activate(self, corroboration: Corroboration) -> None:
        """Publish one corroboration. A later call is a separate activation."""

        if not corroboration.event_ids:
            return
        stamped = self._timestamp()
        self._mark_events(corroboration, stamped)
        self._activate_camera()
        self._write_activation_log(corroboration)

    def _mark_events(self, corroboration: Corroboration, stamped: str) -> None:
        """PATCH every event in the group to the corroborated status."""

        payload = {
            "status": self.CORROBORATED_STATUS,
            "corroborated_at": stamped,
        }
        for event_id in corroboration.event_ids:
            self._client.patch_threat_event(event_id, payload)

    def _activate_camera(self) -> None:
        """PUT the configured camera into Active mode."""

        self._client.put_camera_state(
            self._camera_id,
            {
                "mode": "Active",
                "fps": self.DEFAULT_FPS,
                "resolution": self.DEFAULT_RESOLUTION,
            },
        )

    def _write_activation_log(self, corroboration: Corroboration) -> None:
        """POST one system log describing the camera activation."""

        self._client.post_system_log(
            {
                "event_id": corroboration.event_ids[0],
                "module": self.MODULE_NAME,
                "message": self._log_message(corroboration),
            }
        )

    def _log_message(self, corroboration: Corroboration) -> str:
        """Describe which sources caused the activation."""

        sources = ", ".join(str(source_id) for source_id in corroboration.source_ids)
        return (
            f"Corroborated category {corroboration.category} "
            f"from source_ids {sources}. "
            f"Camera {self._camera_id} set to Active."
        )

    def _timestamp(self) -> str:
        """Return the clock time as a UTC ISO-8601 string."""

        return self._as_utc(self._clock()).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _now() -> datetime:
        """Return the current UTC time."""

        return datetime.now(timezone.utc)

    @staticmethod
    def _as_utc(current: datetime) -> datetime:
        """Return an aware UTC datetime."""

        if current.tzinfo is None:
            return current.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc)
