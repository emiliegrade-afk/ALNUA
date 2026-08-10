"use client";

import { C } from "../app-v2/shared";

/* Onglet placeholder honnête — Phase 38, ROADMAP.md. Pour les sections de
   la maquette d'Emilie (SEO, Brand Center) qui n'ont aucune donnée source
   dans le code aujourd'hui : plutôt que de fabriquer des chiffres ou
   d'omettre silencieusement l'onglet, on l'affiche avec la raison exacte de
   l'absence et ce qu'il faudrait pour le rendre réel. */

export function ComingSoonTab({ title, reason }: { title: string; reason: string }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-3 rounded-2xl border p-10 text-center" style={{ borderColor: C.line, background: "rgba(19,19,22,.5)" }}>
      <span className="flex h-12 w-12 items-center justify-center rounded-full border text-[18px]" style={{ borderColor: "rgba(224,155,106,.35)", color: C.copperLight }}>
        ⏳
      </span>
      <h3 className="text-[15px] font-semibold" style={{ color: C.ivory }}>
        {title} — pas encore disponible
      </h3>
      <p className="max-w-md text-[11.5px] leading-relaxed" style={{ color: C.muted }}>
        {reason}
      </p>
    </div>
  );
}
