"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type SubmitResult = {
  status: "accepted" | "rejected";
  reason?: string;
  confidence?: number;
  priority_score?: number;
  hotspot_id?: string;
};

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [lat, setLat] = useState<string>("");
  const [lng, setLng] = useState<string>("");
  const [locating, setLocating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setPreview(f ? URL.createObjectURL(f) : null);
    setResult(null);
    setError(null);
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by this browser. Please enter coordinates manually.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toString());
        setLng(pos.coords.longitude.toString());
        setLocating(false);
      },
      () => {
        setError("Could not get your location. Please drop a pin manually using the fields below.");
        setLocating(false);
      }
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!file) {
      setError("Please choose a photo.");
      return;
    }
    if (!lat || !lng) {
      setError("Please provide a location (use the button or enter coordinates).");
      return;
    }

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("latitude", lat);
      formData.append("longitude", lng);

      const res = await fetch(`${API_URL}/reports`, {
        method: "POST",
        body: formData,
      });

      if (res.status === 409) {
        setResult({ status: "rejected", reason: "duplicate" });
        return;
      }
      if (res.status === 429) {
        setError("You've submitted too many reports recently. Please try again later.");
        return;
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError("Something went wrong submitting your report. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="max-w-md mx-auto p-6">
      <h1 className="text-xl font-bold mb-4">Report Illegally Dumped Waste</h1>
      <p className="text-sm text-gray-600 mb-6">
        Upload a photo and your location. Reports are anonymous — no account needed.
      </p>

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Photo</label>
          <input type="file" accept="image/*" capture="environment" onChange={onFileChange} className="block w-full" />
          {preview && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="preview" className="mt-2 max-h-64 rounded border object-cover" />
          )}
        </div>

        <div>
          <button
            type="button"
            onClick={useMyLocation}
            disabled={locating}
            className="w-full rounded bg-blue-600 text-white py-2 disabled:opacity-50"
          >
            {locating ? "Getting location…" : "Use My Location"}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium mb-1">Latitude</label>
            <input
              type="number"
              step="any"
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              className="w-full border rounded px-2 py-1"
              placeholder="19.0760"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Longitude</label>
            <input
              type="number"
              step="any"
              value={lng}
              onChange={(e) => setLng(e.target.value)}
              className="w-full border rounded px-2 py-1"
              placeholder="72.8777"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-green-600 text-white py-2 font-semibold disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "Submit Report"}
        </button>
      </form>

      {error && <p className="mt-4 text-red-600 text-sm">{error}</p>}

      {result && result.status === "accepted" && (
        <div className="mt-4 p-3 rounded bg-green-50 border border-green-200 text-sm">
          <p className="font-medium text-green-800">Report accepted — thank you!</p>
          <p>Confidence: {(result.confidence! * 100).toFixed(0)}%</p>
          <p>Hotspot priority score: {result.priority_score?.toFixed(1)}</p>
        </div>
      )}

      {result && result.status === "rejected" && (
        <div className="mt-4 p-3 rounded bg-yellow-50 border border-yellow-200 text-sm">
          <p className="font-medium text-yellow-800">Report not accepted.</p>
          <p>
            Reason: {result.reason === "duplicate" ? "This looks like a duplicate of a recent nearby report." : "No waste detected in the photo."}
          </p>
        </div>
      )}
    </main>
  );
}
