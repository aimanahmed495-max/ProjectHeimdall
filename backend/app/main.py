from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db
from .state import determine_threat_level


app = FastAPI(
    title="Heimdall Core API",
    version="0.1.0",
)


@app.get("/health")
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
)
def create_source(
    source_data: schemas.OsintSourceCreate,
    db: Session = Depends(get_db),
):
    source = models.OsintSource(
        name=source_data.name,
        source_type=source_data.source_type,
        is_active=source_data.is_active,
    )

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


@app.get("/sources", response_model=List[schemas.OsintSourceRead])
def get_sources(db: Session = Depends(get_db)):
    statement = select(models.OsintSource).order_by(models.OsintSource.id)
    return db.scalars(statement).all()

@app.post(
    "/threat-events",
    response_model=schemas.ThreatEventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_threat_event(
    threat_data: schemas.ThreatEventCreate,
    db: Session = Depends(get_db),
):
    source = db.get(models.OsintSource, threat_data.source_id)

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OSINT source not found.",
        )

    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="OSINT source is inactive.",
        )

    threat_event = models.ThreatEvent(
        source_id=threat_data.source_id,
        threat_score=threat_data.threat_score,
        threat_level=determine_threat_level(threat_data.threat_score),
        summary=threat_data.summary,
        event_metadata=threat_data.metadata,
    )

    db.add(threat_event)
    db.commit()
    db.refresh(threat_event)

    return threat_event


@app.get(
    "/threat-events",
    response_model=List[schemas.ThreatEventRead],
)
def get_threat_events(db: Session = Depends(get_db)):
    statement = select(models.ThreatEvent).order_by(
        models.ThreatEvent.threat_score.desc(),
        models.ThreatEvent.created_at.desc(),
    )

    return db.scalars(statement).all()

@app.post(
    "/alert-actions",
    response_model=schemas.AlertActionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_alert_action(
    action_data: schemas.AlertActionCreate,
    db: Session = Depends(get_db),
):
    threat_event = db.get(
        models.ThreatEvent,
        action_data.threat_event_id,
    )

    if threat_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat event not found.",
        )

    alert_action = models.AlertAction(
        threat_event_id=action_data.threat_event_id,
        action_type=action_data.action_type,
        details=action_data.details,
    )

    db.add(alert_action)
    db.commit()
    db.refresh(alert_action)

    return alert_action


@app.get(
    "/alert-actions",
    response_model=List[schemas.AlertActionRead],
)
def get_alert_actions(db: Session = Depends(get_db)):
    statement = select(models.AlertAction).order_by(
        models.AlertAction.created_at.desc()
    )

    return db.scalars(statement).all()