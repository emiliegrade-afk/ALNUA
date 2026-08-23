"use client";

import Link from "next/link";
import { ROUTES } from "@/lib/routes";

const LINKS = [
  { href: ROUTES.hq, label: "Plan HQ", hint: "Carte des bureaux" },
  { href: ROUTES.lounge, label: "Agent Lounge", hint: "Expérimentation · gamification" },
  { href: ROUTES.competition, label: "Compétition", hint: "Classement agents" },
] as const;

/** Always-visible siège life links (competition + lounge were invisible). */
export function SiegeLifeLinks({ className = "" }: { className?: string }) {
  return (
    <nav
      className={`flex flex-wrap gap-2 ${className}`}
      aria-label="Vie du siège"
    >
      {LINKS.map((l) => (
        <Link
          key={l.href}
          href={l.href}
          className="border border-copper/35 px-2.5 py-1.5 text-[11px] tracking-wide text-copper transition hover:border-copper hover:bg-copper/10"
          title={l.hint}
        >
          {l.label}
        </Link>
      ))}
    </nav>
  );
}
