"""initial schema: reports, detections, hotspots

Revision ID: 0001
Revises:
Create Date: 2026-08-17

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.execute(
        """
        CREATE TABLE reports (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            image_url       TEXT NOT NULL,
            image_phash     VARCHAR(64),
            latitude        DOUBLE PRECISION NOT NULL,
            longitude       DOUBLE PRECISION NOT NULL,
            geom            GEOGRAPHY(POINT, 4326) NOT NULL,
            ip_hash         TEXT,
            uploaded_at     TIMESTAMPTZ DEFAULT now(),
            status          VARCHAR(20) DEFAULT 'pending'
        )
        """
    )
    op.execute("CREATE INDEX idx_reports_geom ON reports USING GIST (geom)")
    op.execute("CREATE INDEX idx_reports_phash ON reports (image_phash)")

    op.execute(
        """
        CREATE TABLE detections (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            report_id       UUID REFERENCES reports(id),
            model_version   TEXT,
            is_waste        BOOLEAN,
            confidence      FLOAT,
            severity_score  FLOAT,
            processed_at    TIMESTAMPTZ DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE hotspots (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            centroid        GEOGRAPHY(POINT, 4326),
            report_count    INT DEFAULT 0,
            avg_severity    FLOAT,
            first_seen      TIMESTAMPTZ,
            last_seen       TIMESTAMPTZ,
            priority_score  FLOAT
        )
        """
    )
    op.execute("CREATE INDEX idx_hotspots_geom ON hotspots USING GIST (centroid)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS detections")
    op.execute("DROP TABLE IF EXISTS hotspots")
    op.execute("DROP TABLE IF EXISTS reports")
