from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class OsintSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    source_type: str = Field(min_length=1, max_length=50)
    is_active: bool = True


class OsintSourceRead(BaseModel):
    id: int
    name: str
    source_type: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThreatEventCreate(BaseModel):
    source_id: int = Field(gt=0)
    threat_score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ThreatEventRead(BaseModel):
    id: int
    source_id: int
    threat_score: int
    threat_level: str
    summary: str
    metadata: Dict[str, Any] = Field(validation_alias="event_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)