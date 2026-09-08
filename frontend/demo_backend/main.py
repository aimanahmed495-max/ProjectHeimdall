"""FastAPI mock backend for the Heimdall Sentinel Dashboard prototype.

This service deliberately keeps data in memory. It models the API contract that
the real OSINT/orchestrator backend can implement later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class SystemMode(str, Enum):
    NORMAL = "NORMAL"
    INVESTIGATING = "INVESTIGATING"
    ALERT = "ALERT"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(BaseModel):
    id: str
    title: str
    location: str
    confidence: int = Field(ge=0, le=100)
    severity: str
    status: AlertStatus
    reasoning: list[str]
    created_at: datetime


class DemoAlertRequest(BaseModel):
    title: str = "Possible weapon detected"
    location: str = "East Entrance"
    confidence: int = Field(default=87, ge=0, le=100)


class SystemStatus(BaseModel):
    mode: SystemMode
    osint_engine: str
    camera_controller: str
    active_alerts: int
    updated_at: datetime


class Event(BaseModel):
    type: str
    timestamp: datetime
    data: dict


class ConnectionManager:
    """Tracks dashboard WebSocket connections and broadcasts live events."""

    def __init__(self) -> None:
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, event: Event) -> None:
        disconnected: list[WebSocket] = []
        for connection in self.connections.copy():
            try:
                await connection.send_json(event.model_dump(mode="json"))
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


app = FastAPI(
    title="Heimdall Prototype API",
    description="Mock API and WebSocket server for the Sentinel Dashboard.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()
alerts: list[Alert] = []
current_mode = SystemMode.NORMAL


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_event(event_type: str, data: dict) -> Event:
    return Event(type=event_type, timestamp=utc_now(), data=data)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status", response_model=SystemStatus)
async def get_status() -> SystemStatus:
    active_count = sum(alert.status == AlertStatus.ACTIVE for alert in alerts)
    return SystemStatus(
        mode=current_mode,
        osint_engine="online",
        camera_controller="online",
        active_alerts=active_count,
        updated_at=utc_now(),
    )


@app.get("/api/alerts", response_model=list[Alert])
async def get_alerts() -> list[Alert]:
    return sorted(alerts, key=lambda alert: alert.created_at, reverse=True)


@app.post("/api/demo/alerts", response_model=Alert, status_code=201)
async def create_demo_alert(request: DemoAlertRequest) -> Alert:
    """Simulate the event that the real OSINT engine will eventually produce."""

    global current_mode

    alert = Alert(
        id=str(uuid4()),
        title=request.title,
        location=request.location,
        confidence=request.confidence,
        severity="high" if request.confidence >= 80 else "medium",
        status=AlertStatus.ACTIVE,
        reasoning=[
            "Threat-related keywords matched the monitored topic.",
            "The reported location matched a monitored area.",
            "Confidence exceeded the activation threshold.",
        ],
        created_at=utc_now(),
    )
    alerts.append(alert)
    current_mode = SystemMode.ALERT

    await manager.broadcast(
        make_event("alert.created", alert.model_dump(mode="json"))
    )
    await manager.broadcast(
        make_event(
            "system.mode_changed",
            {
                "previous_mode": SystemMode.NORMAL.value,
                "current_mode": SystemMode.ALERT.value,
                "reason": "Threat confidence exceeded the activation threshold.",
            },
        )
    )
    return alert


@app.patch("/api/alerts/{alert_id}/acknowledge", response_model=Alert)
async def acknowledge_alert(alert_id: str) -> Alert:
    for alert in alerts:
        if alert.id == alert_id:
            alert.status = AlertStatus.ACKNOWLEDGED
            await manager.broadcast(
                make_event(
                    "alert.acknowledged",
                    {"id": alert.id, "status": alert.status.value},
                )
            )
            return alert

    raise HTTPException(status_code=404, detail="Alert not found")


@app.post("/api/demo/reset")
async def reset_demo() -> dict[str, str]:
    global current_mode

    alerts.clear()
    previous_mode = current_mode
    current_mode = SystemMode.NORMAL
    await manager.broadcast(
        make_event(
            "system.mode_changed",
            {
                "previous_mode": previous_mode.value,
                "current_mode": current_mode.value,
                "reason": "Prototype data was reset.",
            },
        )
    )
    return {"status": "reset"}


@app.websocket("/ws/events")
async def events_websocket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        await websocket.send_json(
            make_event(
                "connection.ready",
                {"message": "Connected to the Heimdall event stream."},
            ).model_dump(mode="json")
        )
        while True:
            # Keeping receive active lets FastAPI notice when the browser closes.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
