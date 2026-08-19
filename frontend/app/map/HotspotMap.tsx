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
      {error && (
        <p className="border-b border-[#ee5253]/30 bg-[#ee5253]/[0.08] px-5 py-3 text-sm text-[#ff8a8c]">{error}</p>
      )}
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
              <div className="min-w-[160px] font-sans text-sm">
                <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.12em] text-dim">Hotspot</p>
                <p>Reports: <span className="text-fg">{f.properties.report_count}</span></p>
                <p>Avg severity: <span className="text-fg">{f.properties.avg_severity?.toFixed(1) ?? "n/a"}</span></p>
                <p>Priority score: <span className="text-fg">{f.properties.priority_score?.toFixed(1) ?? "n/a"}</span></p>
                <p>Last seen: <span className="text-fg">{f.properties.last_seen ? new Date(f.properties.last_seen).toLocaleString() : "n/a"}</span></p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
