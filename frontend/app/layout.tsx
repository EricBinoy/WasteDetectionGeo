import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Waste Dumping Reporter",
  description: "Report illegally dumped waste in Mumbai and see hotspots on a map.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <nav className="border-b bg-white px-4 py-3 flex gap-4">
          <Link href="/" className="font-semibold">
            Report Waste
          </Link>
          <Link href="/map" className="font-semibold">
            Hotspot Map
          </Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
