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
    <main className="mx-auto max-w-6xl px-5 py-14 sm:py-20">
      <div className="grid items-start gap-12 lg:grid-cols-[1fr_1fr] lg:gap-16 xl:grid-cols-[1fr_600px]">
        <div className="text-center lg:sticky lg:top-28 lg:text-left">
          <p className="kicker-left mb-6">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan shadow-[0_0_0_4px_rgba(10,189,227,0.16)]" />
            Civic Reporting
          </p>
          <h1 className="font-serif text-4xl font-medium leading-tight text-fg sm:text-5xl lg:text-6xl">
            Report <em className="font-medium italic text-gold">dumped</em> waste
          </h1>
          <p className="mx-auto mt-5 max-w-md text-[15px] leading-relaxed text-muted lg:mx-0">
            Upload a photo and your location. An AI model verifies it before it's added to the map —
            fully anonymous, no account needed.
          </p>
        </div>

        <div>
      <form onSubmit={onSubmit} className="card space-y-6">
        <div>
          <label className="field-label">Photo</label>
          <label
            htmlFor="photo-input"
            className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-line2 bg-white/[0.02] px-4 py-8 text-center transition-colors hover:border-gold/60"
          >
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={preview} alt="preview" className="max-h-56 rounded-xl border border-line object-cover" />
            ) : (
              <>
                <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-dim">Tap to choose or take a photo</span>
                <span className="text-2xl">📷</span>
              </>
            )}
          </label>
          <input
            id="photo-input"
            type="file"
            accept="image/*"
            capture="environment"
            onChange={onFileChange}
            className="hidden"
          />
        </div>

        <button type="button" onClick={useMyLocation} disabled={locating} className="btn-cyan w-full">
          {locating ? "Getting location…" : "Use My Location"}
        </button>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="field-label">Latitude</label>
            <input
              type="number"
              step="any"
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              className="field-input"
              placeholder="19.0760"
            />
          </div>
          <div>
            <label className="field-label">Longitude</label>
            <input
              type="number"
              step="any"
              value={lng}
              onChange={(e) => setLng(e.target.value)}
              className="field-input"
              placeholder="72.8777"
            />
          </div>
        </div>

        <button type="submit" disabled={submitting} className="btn-gold w-full">
          {submitting ? "Submitting…" : "Submit Report"}
        </button>
      </form>

      {error && (
        <div className="mt-5 rounded-2xl border border-[#ee5253]/40 bg-[#ee5253]/[0.08] px-5 py-4 text-sm text-[#ff8a8c]">
          {error}
        </div>
      )}

      {result && result.status === "accepted" && (
        <div className="mt-5 rounded-2xl border border-[#1dd1a1]/40 bg-[#1dd1a1]/[0.08] px-5 py-4">
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#1dd1a1]">Report accepted — thank you</p>
          <div className="mt-3 space-y-1 text-sm text-muted">
            <p>Confidence: <span className="text-fg">{(result.confidence! * 100).toFixed(0)}%</span></p>
            <p>Hotspot priority score: <span className="text-fg">{result.priority_score?.toFixed(1)}</span></p>
          </div>
        </div>
      )}

      {result && result.status === "rejected" && (
        <div className="mt-5 rounded-2xl border border-gold/40 bg-gold/[0.08] px-5 py-4">
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-gold">Report not accepted</p>
          <p className="mt-3 text-sm text-muted">
            {result.reason === "duplicate"
              ? "This looks like a duplicate of a recent nearby report."
              : "No waste detected in the photo."}
          </p>
        </div>
      )}
        </div>
      </div>
    </main>
  );
}
