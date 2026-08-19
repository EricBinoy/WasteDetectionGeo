import dynamic from "next/dynamic";

const HotspotMap = dynamic(() => import("./HotspotMap"), { ssr: false });

export default function MapPage() {
  return (
    <main className="mx-auto max-w-7xl px-5 py-10 sm:px-8">
      <div className="mb-6 text-center">
        <p className="kicker mb-5">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan shadow-[0_0_0_4px_rgba(10,189,227,0.16)]" />
          Live Data
        </p>
        <h1 className="font-serif text-3xl font-medium leading-tight text-fg sm:text-4xl">
          Waste Dumping <em className="italic text-gold">Hotspots</em>
        </h1>
        <p className="mx-auto mt-4 max-w-md text-[15px] leading-relaxed text-muted">
          Verified reports clustered by location, ranked by report count, severity, and recency.
        </p>
      </div>

      <div className="mb-4 flex flex-wrap items-center justify-center gap-4 font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#dc2626]" /> High priority
        </span>
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#f59e0b]" /> Medium
        </span>
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#22c55e]" /> Low
        </span>
      </div>

      <div className="card overflow-hidden !p-0">
        <HotspotMap />
      </div>
    </main>
  );
}
