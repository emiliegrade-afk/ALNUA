"use client";

import { ApiCostsCard } from "@/components/finances/api-costs-card";

/* Onglet "Coûts API" — ApiCostsCard embarqué tel quel (self-fetching,
   LLM/ElevenLabs/manuel 30j déjà réel). Phase 29, ROADMAP.md. */

export function CoutsTab() {
  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-1">
      <ApiCostsCard />
    </div>
  );
}
