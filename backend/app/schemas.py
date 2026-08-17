import uuid
from typing import Optional

from pydantic import BaseModel


class ReportCreateResponse(BaseModel):
    status: str
    report_id: Optional[uuid.UUID] = None
    is_waste: Optional[bool] = None
    confidence: Optional[float] = None
    hotspot_id: Optional[uuid.UUID] = None
    priority_score: Optional[float] = None
    reason: Optional[str] = None


class ReportDetail(BaseModel):
    id: uuid.UUID
    image_url: str
    latitude: float
    longitude: float
    status: str

    class Config:
        from_attributes = True


class HotspotFeatureProperties(BaseModel):
    id: uuid.UUID
    report_count: int
    avg_severity: Optional[float]
    priority_score: Optional[float]
    first_seen: Optional[str]
    last_seen: Optional[str]
