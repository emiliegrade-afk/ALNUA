"use client";

import Link from "next/link";
import { ROUTES } from "@/lib/routes";
import { C } from "../app-v2/shared";

/* Pas de réglages propres au workshop Robotique aujourd'hui — plutôt
 * qu'inventer un panneau, on renvoie vers les vrais réglages du Hub. */
export function SettingsTab() {
  return (
    <div className="flex min-h-[220px] flex-1 flex-col items-center justify-center gap-3 rounded-xl border text-center" style={{ borderColor: C.line, color: C.faint }}>
      <p className="text-[11px]">Pas encore de réglages spécifiques au workshop Robotique.</p>
      <Link href={ROUTES.settings} className="rounded-lg border px-3 py-1.5 text-[10.5px]" style={{ borderColor: "rgba(192,138,114,.3)", color: C.copperLight }}>
        Ouvrir les réglages du Hub ↗
      </Link>
    </div>
  );
}
