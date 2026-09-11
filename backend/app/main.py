from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db


app = FastAPI(
    title="Heimdall Core API",
    version="0.2.0",
    description="Prototype API following Heimdall's five-table report design.",
)


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }


@app.post(
    "/sources",
    response_model=schemas.OsintSourceRead,
    status_code=status.HTTP_201_CREATED,
    tags=["OSINT Sources"],
)
def create_source(
    source_data: schemas.OsintSourceCreate,
    db: Session = Depends(get_db),
):
    source = models.OsintSource(**source_data.model_dump())
    db.add(source)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A source with this name already exists.",
        )

    db.refresh(source)
    return source


@app.get(
    "/sources",
    response_model=List[schemas.OsintSourceRead],
    tags=["OSINT Sources"],
)
def get_sources(db: Session = Depends(get_db)):
    statement = select(models.OsintSource).order_by(
        models.OsintSource.source_id
    )
    return db.scalars(statement).all()


@app.post(
    "/threat-events",
    response_model=schemas.ThreatEventRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Threat Events"],
)
def create_threat_event(
    threat_data: schemas.ThreatEventCreate,
    db: Session = Depends(get_db),
):
    threat_event = models.ThreatEvent(**threat_data.model_dump())

    db.add(threat_event)
    db.commit()
    db.refresh(threat_event)

    return threat_event


@app.get(
    "/threat-events",
    response_model=List[schemas.ThreatEventRead],
    tags=["Threat Events"],
)
def get_threat_events(db: Session = Depends(get_db)):
    statement = select(models.ThreatEvent).order_by(
        models.ThreatEvent.timestamp.desc(),
    )
    return db.scalars(statement).all()


@app.post(
    "/alert-logs",
    response_model=schemas.AlertLogRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Alert Logs"],
)
def create_alert_log(
    alert_data: schemas.AlertLogCreate,
    db: Session = Depends(get_db),
):
    threat_event = db.get(models.ThreatEvent, alert_data.event_id)

    if threat_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat event not found.",
        )

    alert_log = models.AlertLog(**alert_data.model_dump())

    db.add(alert_log)
    db.commit()
    db.refresh(alert_log)

    return alert_log


@app.get(
    "/alert-logs",
    response_model=List[schemas.AlertLogRead],
    tags=["Alert Logs"],
)
def get_alert_logs(db: Session = Depends(get_db)):
    statement = select(models.AlertLog).order_by(
        models.AlertLog.alert_time.desc(),
    )
    return db.scalars(statement).all()


@app.post(
    "/camera-states",
    response_model=schemas.CameraStateRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Camera States"],
)
def create_camera_state(
    camera_data: schemas.CameraStateCreate,
    db: Session = Depends(get_db),
):
    camera_state = models.CameraState(**camera_data.model_dump())

    db.add(camera_state)
    db.commit()
    db.refresh(camera_state)

    return camera_state


@app.get(
    "/camera-states",
    response_model=List[schemas.CameraStateRead],
    tags=["Camera States"],
)
def get_camera_states(db: Session = Depends(get_db)):
    statement = select(models.CameraState).order_by(
        models.CameraState.timestamp.desc(),
    )
    return db.scalars(statement).all()


@app.post(
    "/system-logs",
    response_model=schemas.SystemLogRead,
    status_code=status.HTTP_201_CREATED,
    tags=["System Logs"],
)
def create_system_log(
    log_data: schemas.SystemLogCreate,
    db: Session = Depends(get_db),
):
    if log_data.event_id is not None:
        threat_event = db.get(models.ThreatEvent, log_data.event_id)

        if threat_event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Threat event not found.",
            )

    system_log = models.SystemLog(**log_data.model_dump())

    db.add(system_log)
    db.commit()
    db.refresh(system_log)

    return system_log


@app.get(
    "/system-logs",
    response_model=List[schemas.SystemLogRead],
    tags=["System Logs"],
)
def get_system_logs(db: Session = Depends(get_db)):
    statement = select(models.SystemLog).order_by(
        models.SystemLog.log_time.desc(),
    )
    return db.scalars(statement).all()