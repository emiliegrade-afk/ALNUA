"use client";

import Link from "next/link";
import { BookOpen } from "lucide-react";
import { ROUTES } from "@/lib/routes";

/** Pin guides Hub en tête de Bibliothèque (≠ fiches de recherche agents). */
export function LibraryHubManualCard() {
  return (
    <Link
      href={ROUTES.userManual}
      className="flex items-start gap-3 rounded-xl border border-copper/20 bg-obsidian-deep/40 px-4 py-3 transition hover:border-copper/40"
    >
      <BookOpen className="mt-0.5 h-4 w-4 shrink-0 text-copper" />
      <div className="min-w-0">
        <p className="text-sm font-medium text-ivory/90">Manuel utilisateur ALNUA Hub</p>
        <p className="mt-0.5 text-[11px] text-titanium/60">
          Mode d&apos;emploi CEO (écrans, arbres, sécurité) — aussi depuis le bureau CEO et{" "}
          <span className="text-copper/80">Documents</span>.
        </p>
      </div>
    </Link>
  );
}
