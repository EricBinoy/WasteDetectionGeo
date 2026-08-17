"""PostGIS-backed hotspot clustering.

Clustering strategy: on each accepted report, look for an existing hotspot whose centroid is
within HOTSPOT_RADIUS_METERS. If found, fold the new point into a running-average centroid and
bump its stats. Otherwise create a new hotspot seeded at the report's location. This is a simple
greedy/incremental clustering approach (not full re-clustering) which is good enough for an MVP.
"""
import math
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Hotspot

HOTSPOT_RADIUS_METERS = 100
RECENCY_DECAY_DAYS = 7  # weight halves roughly every this many days


def _recency_weight(last_seen: datetime) -> float:
    now = datetime.now(timezone.utc)
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    days_since = max(0.0, (now - last_seen).total_seconds() / 86400.0)
    # Exponential decay on a 0-100 scale, matching report_count/avg_severity's rough magnitude.
    return 100.0 * math.exp(-days_since / RECENCY_DECAY_DAYS)


def _priority_score(report_count: int, avg_severity: float, last_seen: datetime) -> float:
    return report_count * 0.4 + avg_severity * 0.4 + _recency_weight(last_seen) * 0.2


def find_nearby_hotspot(db: Session, latitude: float, longitude: float) -> Hotspot | None:
    row = db.execute(
        text(
            """
            SELECT id FROM hotspots
            WHERE ST_DWithin(centroid, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
            ORDER BY ST_Distance(centroid, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography)
            LIMIT 1
            """
        ),
        {"lng": longitude, "lat": latitude, "radius": HOTSPOT_RADIUS_METERS},
    ).fetchone()
    if row is None:
        return None
    return db.query(Hotspot).filter(Hotspot.id == row.id).first()


def upsert_hotspot(db: Session, latitude: float, longitude: float, severity_score: float) -> Hotspot:
    now = datetime.now(timezone.utc)
    hotspot = find_nearby_hotspot(db, latitude, longitude)

    if hotspot is None:
        hotspot = Hotspot(
            report_count=1,
            avg_severity=severity_score,
            first_seen=now,
            last_seen=now,
        )
        db.add(hotspot)
        db.flush()
        db.execute(
            text("UPDATE hotspots SET centroid = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography WHERE id = :id"),
            {"lng": longitude, "lat": latitude, "id": hotspot.id},
        )
    else:
        old_count = hotspot.report_count or 0
        new_count = old_count + 1

        centroid_row = db.execute(
            text("SELECT ST_X(centroid::geometry) AS lng, ST_Y(centroid::geometry) AS lat FROM hotspots WHERE id = :id"),
            {"id": hotspot.id},
        ).fetchone()
        new_lat = (centroid_row.lat * old_count + latitude) / new_count
        new_lng = (centroid_row.lng * old_count + longitude) / new_count

        hotspot.avg_severity = ((hotspot.avg_severity or 0) * old_count + severity_score) / new_count
        hotspot.report_count = new_count
        hotspot.last_seen = now

        db.execute(
            text("UPDATE hotspots SET centroid = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography WHERE id = :id"),
            {"lng": new_lng, "lat": new_lat, "id": hotspot.id},
        )

    hotspot.priority_score = _priority_score(hotspot.report_count, hotspot.avg_severity, hotspot.last_seen)
    db.flush()
    return hotspot


def hotspots_as_geojson(db: Session) -> dict:
    rows = db.execute(
        text(
            """
            SELECT id, ST_X(centroid::geometry) AS lng, ST_Y(centroid::geometry) AS lat,
                   report_count, avg_severity, priority_score, first_seen, last_seen
            FROM hotspots
            """
        )
    ).fetchall()

    features = []
    for row in rows:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row.lng, row.lat]},
                "properties": {
                    "id": str(row.id),
                    "report_count": row.report_count,
                    "avg_severity": row.avg_severity,
                    "priority_score": row.priority_score,
                    "first_seen": row.first_seen.isoformat() if row.first_seen else None,
                    "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
