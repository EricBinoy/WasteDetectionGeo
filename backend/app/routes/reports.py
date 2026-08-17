import hashlib
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.cv_pipeline import classify_image
from app.db import get_db
from app.dedup import compute_phash, is_near_duplicate
from app.geo import hotspots_as_geojson, upsert_hotspot
from app.models import Detection, Report
from app.rate_limit import limiter
from app.schemas import ReportCreateResponse, ReportDetail

router = APIRouter()

MIN_CONFIDENCE = 0.5


@router.post("/reports", response_model=ReportCreateResponse)
@limiter.limit("10/hour")
async def create_report(
    request: Request,
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: Session = Depends(get_db),
):
    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(image.filename or "")[1] or ".jpg"
    stored_name = f"{uuid.uuid4()}{ext}"
    stored_path = os.path.join(settings.upload_dir, stored_name)

    contents = await image.read()
    with open(stored_path, "wb") as f:
        f.write(contents)

    image_url = f"{settings.public_base_url}/uploads/{stored_name}"
    phash = compute_phash(stored_path)

    if is_near_duplicate(db, phash, latitude, longitude):
        raise HTTPException(status_code=409, detail={"status": "rejected", "reason": "duplicate"})

    ip_hash = hashlib.sha256((request.client.host or "unknown").encode()).hexdigest()

    report = Report(
        image_url=image_url,
        image_phash=phash,
        latitude=latitude,
        longitude=longitude,
        ip_hash=ip_hash,
        status="pending",
    )
    db.add(report)
    db.flush()
    db.execute(
        text("UPDATE reports SET geom = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography WHERE id = :id"),
        {"lng": longitude, "lat": latitude, "id": report.id},
    )

    classification = classify_image(stored_path)

    if not classification.is_waste or classification.confidence < MIN_CONFIDENCE:
        report.status = "rejected"
        db.add(
            Detection(
                report_id=report.id,
                model_version="nonamelife/garbage-detection-model",
                is_waste=classification.is_waste,
                confidence=classification.confidence,
                severity_score=0.0,
            )
        )
        db.commit()
        return ReportCreateResponse(
            status="rejected",
            reason="no_waste_detected",
            confidence=classification.confidence,
            report_id=report.id,
            is_waste=classification.is_waste,
        )

    # Placeholder severity: confidence-weighted. TODO once a real detection (bounding-box) model
    # replaces this classifier, factor in the fraction of the frame covered by waste.
    severity_score = classification.confidence * 100

    report.status = "accepted"
    db.add(
        Detection(
            report_id=report.id,
            model_version="nonamelife/garbage-detection-model",
            is_waste=classification.is_waste,
            confidence=classification.confidence,
            severity_score=severity_score,
        )
    )

    hotspot = upsert_hotspot(db, latitude, longitude, severity_score)
    db.commit()

    return ReportCreateResponse(
        status="accepted",
        report_id=report.id,
        is_waste=classification.is_waste,
        confidence=classification.confidence,
        hotspot_id=hotspot.id,
        priority_score=hotspot.priority_score,
    )


@router.get("/hotspots")
def get_hotspots(db: Session = Depends(get_db)):
    return hotspots_as_geojson(db)


@router.get("/reports/{report_id}", response_model=ReportDetail)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return report
