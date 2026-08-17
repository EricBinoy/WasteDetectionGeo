"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Mumbai city center, used as the default map view.
const MUMBAI_CENTER: [number, number] = [19.076, 72.8777];

type HotspotFeature = {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: {
    id: string;
    report_count: number;
    avg_severity: number | null;
    priority_score: number | null;
    first_seen: string | null;
    last_seen: string | null;
  };
};

function colorForPriority(score: number | null): string {
  if (score === null) return "#9ca3af";
  if (score >= 66) return "#dc2626"; // red - high priority
  if (score >= 33) return "#f59e0b"; // amber - medium
  return "#22c55e"; // green - low
}

export default function HotspotMap() {
  const [features, setFeatures] = useState<HotspotFeature[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/hotspots`)
      .then((res) => res.json())
      .then((geojson) => setFeatures(geojson.features ?? []))
      .catch(() => setError("Could not load hotspots from the backend."));
  }, []);

  return (
    <div>
      {error && <p className="text-red-600 mb-2 text-sm">{error}</p>}
      <MapContainer center={MUMBAI_CENTER} zoom={12} style={{ height: "70vh", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {features.map((f) => (
          <CircleMarker
            key={f.properties.id}
            center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
            radius={8 + Math.min(f.properties.report_count, 20)}
            pathOptions={{
              color: colorForPriority(f.properties.priority_score),
              fillColor: colorForPriority(f.properties.priority_score),
              fillOpacity: 0.6,
            }}
          >
            <Popup>
              <div className="text-sm">
                <p>Reports: {f.properties.report_count}</p>
                <p>Avg severity: {f.properties.avg_severity?.toFixed(1) ?? "n/a"}</p>
                <p>Priority score: {f.properties.priority_score?.toFixed(1) ?? "n/a"}</p>
                <p>Last seen: {f.properties.last_seen ? new Date(f.properties.last_seen).toLocaleString() : "n/a"}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
