from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OsintSourceCreate(BaseModel):
    source_name: str = Field(min_length=1, max_length=100)
    source_type: str = Field(min_length=1, max_length=50)
    url: str = Field(min_length=1)
    reliability_score: float = Field(ge=0, le=1)


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )
    password: str = Field(min_length=12, max_length=128)


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    user_id: int
    username: str
    is_active: bool
    created_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OsintSourceRead(OsintSourceCreate):
    source_id: int

    model_config = ConfigDict(from_attributes=True)


class ThreatEventCreate(BaseModel):
    source_id: Optional[int] = Field(default=None, gt=0)
    object_class: str = Field(min_length=1, max_length=100)
    confidence_score: float = Field(ge=0, le=1)
    camera_id: int = Field(gt=0)
    status: str = Field(
        default="Pending",
        min_length=1,
        max_length=30,
    )


class ThreatEventRead(ThreatEventCreate):
    event_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertLogCreate(BaseModel):
    event_id: int = Field(gt=0)
    alert_level: str = Field(min_length=1, max_length=30)
    message: str = Field(min_length=1)
    acknowledged: bool = False


class AlertLogRead(AlertLogCreate):
    alert_id: int
    alert_time: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraStateBase(BaseModel):
    mode: str = Field(
        min_length=1,
        max_length=20,
        pattern="^(Dormant|Active)$",
    )
    fps: int = Field(gt=0)
    resolution: str = Field(min_length=1, max_length=30)


class CameraStateCreate(CameraStateBase):
    camera_id: int = Field(gt=0)


class CameraStateUpdate(CameraStateBase):
    pass


class CameraStateRead(CameraStateCreate):
    state_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemLogCreate(BaseModel):
    event_id: Optional[int] = Field(default=None, gt=0)
    module: str = Field(min_length=1, max_length=50)
    message: str = Field(min_length=1)


class SystemLogRead(SystemLogCreate):
    log_id: int
    log_time: datetime

    model_config = ConfigDict(from_attributes=True)
