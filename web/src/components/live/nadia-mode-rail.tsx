"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: ROUTES.live, label: "Live" },
  { href: ROUTES.secretary, label: "Bureau" },
  { href: ROUTES.connections, label: "Connexions" },
] as const;

/** Quick jumps between Nadia surfaces (mobile-first horizontal bar). */
export function NadiaModeRail({ className }: { className?: string }) {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Espaces Nadia"
      className={cn(
        "flex gap-1 overflow-x-auto rounded-xl border border-copper/20 bg-obsidian-2/80 p-1",
        className,
      )}
    >
      {LINKS.map(({ href, label }) => {
        const active = pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium transition",
              active
                ? "bg-copper/25 text-copper-glow"
                : "text-titanium hover:bg-obsidian-deep/60 hover:text-ivory",
            )}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
