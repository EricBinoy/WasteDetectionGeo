"""Perceptual-hash based near-duplicate detection for reports uploaded from the same spot."""
from datetime import datetime, timedelta, timezone

import imagehash
from PIL import Image
from sqlalchemy import text
from sqlalchemy.orm import Session

DEDUP_RADIUS_METERS = 50
DEDUP_WINDOW_HOURS = 24
HAMMING_DISTANCE_THRESHOLD = 6


def compute_phash(image_path: str) -> str:
    with Image.open(image_path) as img:
        return str(imagehash.phash(img))


def is_near_duplicate(db: Session, phash: str, latitude: float, longitude: float) -> bool:
    """Checks recent reports within DEDUP_RADIUS_METERS for a phash within HAMMING_DISTANCE_THRESHOLD."""
    since = datetime.now(timezone.utc) - timedelta(hours=DEDUP_WINDOW_HOURS)

    rows = db.execute(
        text(
            """
            SELECT image_phash FROM reports
            WHERE image_phash IS NOT NULL
              AND uploaded_at >= :since
              AND ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
            """
        ),
        {"since": since, "lng": longitude, "lat": latitude, "radius": DEDUP_RADIUS_METERS},
    ).fetchall()

    candidate_hash = imagehash.hex_to_hash(phash)
    for row in rows:
        try:
            existing_hash = imagehash.hex_to_hash(row.image_phash)
        except (TypeError, ValueError):
            continue
        if (candidate_hash - existing_hash) < HAMMING_DISTANCE_THRESHOLD:
            return True
    return False
