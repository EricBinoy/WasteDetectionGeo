"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/", label: "Report" },
  { href: "/map", label: "Map" },
];

export default function NavToggle() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-1 rounded-full border border-line2 bg-white/[0.04] p-1">
      {TABS.map((tab) => {
        const active = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`rounded-full px-4 py-2 font-mono text-[11px] uppercase tracking-[0.08em] transition-colors ${
              active ? "bg-gradient-to-br from-cyan to-[#7fe3f5] font-bold text-ink" : "text-muted hover:text-fg"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
