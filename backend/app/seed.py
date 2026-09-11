from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .database import SessionLocal


class DatabaseSeeder:
    """Insert fake Heimdall rows for local development and demos.

    Seed data is identified by stable field values so ``run()`` can be
    executed more than once without duplicating rows or violating unique
    constraints.
    """

    OSINT_SOURCES: List[Dict[str, Any]] = [
        {
            "source_name": "Demo District 4 Scanner",
            "source_type": "Public Scanner",
            "url": "https://example.com/demo/district-4-scanner",
            "reliability_score": 0.75,
        },
        {
            "source_name": "Demo Neighborhood Watch",
            "source_type": "Community Report",
            "url": "https://example.com/demo/neighborhood-watch",
            "reliability_score": 0.5,
        },
        {
            "source_name": "Demo Local News Crime Desk",
            "source_type": "News RSS",
            "url": "https://example.com/demo/local-news-crime",
            "reliability_score": 0.625,
        },
        {
            "source_name": "Demo Campus Safety Bulletin",
            "source_type": "Public Bulletin",
            "url": "https://example.com/demo/campus-safety",
            "reliability_score": 0.875,
        },
    ]

    THREAT_EVENTS: List[Dict[str, Any]] = [
        {
            "object_class": "person",
            "confidence_score": 0.875,
            "camera_id": 1,
            "status": "Pending",
        },
        {
            "object_class": "vehicle",
            "confidence_score": 0.75,
            "camera_id": 1,
            "status": "Pending",
        },
        {
            "object_class": "unknown",
            "confidence_score": 0.25,
            "camera_id": 2,
            "status": "Pending",
        },
        {
            "object_class": "person",
            "confidence_score": 0.625,
            "camera_id": 2,
            "status": "Pending",
        },
        {
            "object_class": "vehicle",
            "confidence_score": 0.5,
            "camera_id": 2,
            "status": "Pending",
        },
        {
            "object_class": "unknown",
            "confidence_score": 0.125,
            "camera_id": 3,
            "status": "Pending",
        },
    ]

    CAMERA_STATES: List[Dict[str, Any]] = [
        {
            "camera_id": 1,
            "mode": "Active",
            "fps": 15,
            "resolution": "1080p",
        },
        {
            "camera_id": 2,
            "mode": "Dormant",
            "fps": 5,
            "resolution": "720p",
        },
    ]

    def __init__(self, session: Session) -> None:
        """Attach a SQLAlchemy session used for all seed writes.

        Args:
            session: Open ``SessionLocal`` instance. The caller owns
                session lifetime; ``run()`` commits on success.
        """

        self._session = session
        self._inserted = {
            "osint_sources": 0,
            "camera_states": 0,
            "threat_events": 0,
            "alert_logs": 0,
            "system_logs": 0,
        }
        self._skipped = {
            "osint_sources": 0,
            "camera_states": 0,
            "threat_events": 0,
            "alert_logs": 0,
            "system_logs": 0,
        }
        self._threat_events: List[models.ThreatEvent] = []

    def run(self) -> None:
        """Seed every table in foreign-key order and print a summary.

        Sources and camera states are written first. Threat events are
        written next so alert logs and system logs can use returned
        ``event_id`` values instead of guessing IDs.
        """

        self.seed_osint_sources()
        self.seed_camera_states()
        self.seed_threat_events()
        self.seed_alert_logs()
        self.seed_system_logs()
        self._session.commit()
        self._print_summary()

    def seed_osint_sources(self) -> None:
        """Insert demo OSINT sources, skipping names that already exist."""

        for payload in self.OSINT_SOURCES:
            existing = self._session.scalar(
                select(models.OsintSource).where(
                    models.OsintSource.source_name == payload["source_name"],
                )
            )
            if existing is not None:
                self._skipped["osint_sources"] += 1
                continue

            self._session.add(models.OsintSource(**payload))
            self._inserted["osint_sources"] += 1

    def seed_camera_states(self) -> None:
        """Insert demo camera states for two cameras if they are missing."""

        for payload in self.CAMERA_STATES:
            existing = self._session.scalar(
                select(models.CameraState).where(
                    models.CameraState.camera_id == payload["camera_id"],
                    models.CameraState.mode == payload["mode"],
                    models.CameraState.fps == payload["fps"],
                    models.CameraState.resolution == payload["resolution"],
                )
            )
            if existing is not None:
                self._skipped["camera_states"] += 1
                continue

            self._session.add(models.CameraState(**payload))
            self._inserted["camera_states"] += 1

    def seed_threat_events(self) -> List[models.ThreatEvent]:
        """Insert demo threat events and keep the rows for later foreign keys.

        Each seed event uses a unique combination of object class,
        confidence score, camera ID, and status so a second run can find
        the same rows instead of inserting duplicates.

        Returns:
            The seeded threat events in definition order, including rows
            that already existed.
        """

        events: List[models.ThreatEvent] = []

        for payload in self.THREAT_EVENTS:
            existing = self._session.scalar(
                select(models.ThreatEvent).where(
                    models.ThreatEvent.object_class == payload["object_class"],
                    models.ThreatEvent.confidence_score
                    == payload["confidence_score"],
                    models.ThreatEvent.camera_id == payload["camera_id"],
                    models.ThreatEvent.status == payload["status"],
                )
            )
            if existing is not None:
                self._skipped["threat_events"] += 1
                events.append(existing)
                continue

            event = models.ThreatEvent(**payload)
            self._session.add(event)
            self._inserted["threat_events"] += 1
            events.append(event)

        self._session.flush()
        self._threat_events = events
        return events

    def seed_alert_logs(self) -> None:
        """Insert demo alerts attached to seeded threat events."""

        if len(self._threat_events) < 3:
            return

        alert_specs: List[Tuple[int, Dict[str, Any]]] = [
            (
                0,
                {
                    "alert_level": "Critical",
                    "message": (
                        "Demo alert: high-confidence person near camera 1"
                    ),
                    "acknowledged": False,
                },
            ),
            (
                1,
                {
                    "alert_level": "Warning",
                    "message": (
                        "Demo alert: vehicle lingering in the south lot"
                    ),
                    "acknowledged": False,
                },
            ),
            (
                2,
                {
                    "alert_level": "Info",
                    "message": (
                        "Demo alert: unclassified motion on camera 2"
                    ),
                    "acknowledged": True,
                },
            ),
        ]

        for event_index, payload in alert_specs:
            event = self._threat_events[event_index]
            existing = self._session.scalar(
                select(models.AlertLog).where(
                    models.AlertLog.event_id == event.event_id,
                    models.AlertLog.message == payload["message"],
                )
            )
            if existing is not None:
                self._skipped["alert_logs"] += 1
                continue

            self._session.add(
                models.AlertLog(event_id=event.event_id, **payload)
            )
            self._inserted["alert_logs"] += 1

    def seed_system_logs(self) -> None:
        """Insert demo system logs, some linked to threat events."""

        linked_event_id: Optional[int] = None
        second_event_id: Optional[int] = None
        if self._threat_events:
            linked_event_id = self._threat_events[0].event_id
        if len(self._threat_events) > 1:
            second_event_id = self._threat_events[1].event_id

        log_specs: List[Dict[str, Any]] = [
            {
                "event_id": linked_event_id,
                "module": "vision",
                "message": "Demo: YOLOv8 posted a person detection",
            },
            {
                "event_id": second_event_id,
                "module": "osint-agent",
                "message": (
                    "Demo: OSINT classified a nearby break-in report"
                ),
            },
            {
                "event_id": None,
                "module": "vision",
                "message": "Demo: camera pipeline started",
            },
            {
                "event_id": None,
                "module": "osint-agent",
                "message": "Demo: OSINT polling started",
            },
        ]

        for payload in log_specs:
            existing = self._session.scalar(
                select(models.SystemLog).where(
                    models.SystemLog.module == payload["module"],
                    models.SystemLog.message == payload["message"],
                )
            )
            if existing is not None:
                self._skipped["system_logs"] += 1
                continue

            self._session.add(models.SystemLog(**payload))
            self._inserted["system_logs"] += 1

    def _print_summary(self) -> None:
        """Print inserted vs skipped counts for each table."""

        print("Heimdall database seed")
        for table_name in (
            "osint_sources",
            "camera_states",
            "threat_events",
            "alert_logs",
            "system_logs",
        ):
            inserted = self._inserted[table_name]
            skipped = self._skipped[table_name]
            print(
                f"  {table_name}: inserted {inserted}, skipped {skipped}"
            )
        print("Done.")


if __name__ == "__main__":
    session = SessionLocal()

    try:
        DatabaseSeeder(session).run()
    finally:
        session.close()
