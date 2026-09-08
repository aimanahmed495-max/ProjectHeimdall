from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class OsintSource(Base):
    __tablename__ = "osint_sources"
    __table_args__ = (
        CheckConstraint(
            "reliability_score >= 0 AND reliability_score <= 1",
            name="ck_osint_sources_reliability_range",
        ),
    )

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    reliability_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )


class ThreatEvent(Base):
    __tablename__ = "threat_events"
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_threat_events_confidence_range",
        ),
    )

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    object_class: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    camera_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Pending",
        server_default="Pending",
        index=True,
    )

    alert_logs: Mapped[List["AlertLog"]] = relationship(
        back_populates="threat_event",
        cascade="all, delete-orphan",
    )
    system_logs: Mapped[List["SystemLog"]] = relationship(
        back_populates="threat_event",
    )


class AlertLog(Base):
    __tablename__ = "alert_logs"

    alert_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("threat_events.event_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    alert_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    threat_event: Mapped["ThreatEvent"] = relationship(
        back_populates="alert_logs",
    )


class CameraState(Base):
    __tablename__ = "camera_states"

    state_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    camera_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    fps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    resolution: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class SystemLog(Base):
    __tablename__ = "system_logs"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("threat_events.event_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    log_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    module: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    threat_event: Mapped[Optional["ThreatEvent"]] = relationship(
        back_populates="system_logs",
    )