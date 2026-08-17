import uuid

from geoalchemy2 import Geography
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_url = Column(String, nullable=False)
    image_phash = Column(String(64))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    ip_hash = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="pending")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"))
    model_version = Column(String)
    is_waste = Column(Boolean)
    confidence = Column(Float)
    severity_score = Column(Float)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())


class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    centroid = Column(Geography(geometry_type="POINT", srid=4326))
    report_count = Column(Integer, default=0)
    avg_severity = Column(Float)
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    priority_score = Column(Float)
