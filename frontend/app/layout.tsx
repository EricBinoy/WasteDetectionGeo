import type { Metadata } from "next";
import Link from "next/link";
import { Fraunces, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import NavToggle from "./NavToggle";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["500", "600"],
  style: ["normal", "italic"],
  variable: "--font-fraunces",
});
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-space-grotesk",
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-jetbrains",
});

export const metadata: Metadata = {
  title: "Waste Watch",
  description: "Report illegally dumped waste in Mumbai and see hotspots on a map.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-ink font-sans text-fg">
        <header className="sticky top-0 z-50 flex items-center justify-between gap-4 border-b border-line bg-ink/85 px-5 py-4 backdrop-blur-md">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="h-2 w-2 rounded-full bg-cyan shadow-[0_0_0_4px_rgba(10,189,227,0.18)]" />
            <span className="font-mono text-[11px] font-bold uppercase tracking-[0.12em]">Waste Watch</span>
          </Link>
          <NavToggle />
        </header>
        {children}
      </body>
    </html>
  );
}
