"use client";

import Link from "next/link";
import { BookOpen } from "lucide-react";
import { ROUTES } from "@/lib/routes";
import { C } from "@/app/app-v2/shared";

/** Entrée visible sur le bureau CEO → manuel noob rendu dans le Hub. */
export function CeoUserManualCard() {
  return (
    <Link
      href={ROUTES.userManual}
      className="flex items-start gap-3 rounded-xl border px-4 py-3 transition"
      style={{
        borderColor: C.copperLine,
        background: "transparent",
      }}
    >
      <BookOpen className="mt-0.5 h-4 w-4 shrink-0" style={{ color: C.copper }} />
      <div className="min-w-0">
        <p className="text-sm font-medium" style={{ color: C.ivory }}>
          Manuel d&apos;utilisation
        </p>
        <p className="mt-0.5 text-[11px]" style={{ color: C.dim }}>
          Guide noob — écrans, pôles, arbres R&amp;D, quotidien, dépannage. Ouvre dans le Hub.
        </p>
      </div>
    </Link>
  );
}
