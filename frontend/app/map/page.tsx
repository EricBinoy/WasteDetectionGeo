import dynamic from "next/dynamic";

const HotspotMap = dynamic(() => import("./HotspotMap"), { ssr: false });

export default function MapPage() {
  return (
    <main className="p-4">
      <h1 className="text-xl font-bold mb-4">Waste Dumping Hotspots</h1>
      <HotspotMap />
    </main>
  );
}
