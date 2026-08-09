"use client";

import { useEffect, useState } from "react";
import { fetchLatestFunnelSnapshot, type FunnelSnapshot } from "@/lib/marketing-funnel-api";
import { FunnelEntryModal } from "@/components/marketing/funnel-entry-modal";
import type { Project } from "@/lib/types";
import { C } from "@/app/app-v2/shared";
import { PremiumPanel, FunnelBars } from "@/app/marketing-v2/premium";

/* "Entonnoir de conversion" — Phase 37, ROADMAP.md (échelle premium, Phase
   38). Saisie mensuelle manuelle par produit (Visiteurs → Intéressés →
   Engagés → Abonnés → Clients) : aucun tracking automatique côté Hub, la
   vraie source vit dans les analytics propres à chaque produit (App Store
   Connect, Play Console, Plausible/GA4, signups Supabase). source_note
   documente d'où vient le chiffre pour rester auditable — jamais une
   extrapolation. */

const STAGES = [
  { key: "visitors", label: "Visiteurs" },
  { key: "interested", label: "Intéressés" },
  { key: "engaged", label: "Engagés" },
  { key: "subscribers", label: "Abonnés" },
  { key: "customers", label: "Clients" },
] as const;

export function ConversionFunnelPanel({ projects }: { projects: Project[] }) {
  const [projectId, setProjectId] = useState<string>("");
  const [snapshot, setSnapshot] = useState<FunnelSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [entryOpen, setEntryOpen] = useState(false);

  useEffect(() => {
    if (!projectId && projects.length > 0) setProjectId(projects[0].id);
  }, [projects, projectId]);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    setLoading(true);
    fetchLatestFunnelSnapshot(projectId)
      .then((s) => {
        if (!cancelled) setSnapshot(s);
      })
      .catch(() => {
        if (!cancelled) setSnapshot(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  return (
    <PremiumPanel
      title="Entonnoir de conversion"
      action={
        projects.length > 0 ? (
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="rounded-md border bg-transparent px-2 py-1 text-[11px]"
            style={{ borderColor: C.line, color: C.warm }}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id} style={{ background: "#181410" }}>
                {p.name}
              </option>
            ))}
          </select>
        ) : undefined
      }
    >
      {projects.length === 0 ? (
        <p className="text-[11px]" style={{ color: C.faint }}>
          Aucun produit disponible.
        </p>
      ) : loading ? (
        <p className="text-[11px]" style={{ color: C.faint }}>
          Chargement…
        </p>
      ) : !snapshot ? (
        <div>
          <p className="text-[11px] leading-relaxed" style={{ color: C.faint }}>
            Aucun chiffre saisi pour ce produit ce mois-ci. Source attendue : App Store Connect /
            Play Console / Plausible / GA4 / signups Supabase.
          </p>
          <button
            type="button"
            onClick={() => setEntryOpen(true)}
            className="mt-3 rounded-lg border px-3 py-1.5 text-[11px]"
            style={{ borderColor: C.lineStrong, color: C.copperLight }}
          >
            Saisir les chiffres du mois
          </button>
        </div>
      ) : (
        <div>
          <FunnelBars stages={STAGES.map((s) => ({ label: s.label, value: snapshot[s.key] }))} />
          <div className="mt-3 flex items-center justify-between">
            <p className="text-[10px]" style={{ color: C.faint }}>
              {new Date(snapshot.period_month).toLocaleDateString("fr-FR", { month: "long", year: "numeric" })}
              {snapshot.source_note ? ` · ${snapshot.source_note}` : ""}
            </p>
            <button
              type="button"
              onClick={() => setEntryOpen(true)}
              className="text-[11px]"
              style={{ color: C.copperLight }}
            >
              Mettre à jour →
            </button>
          </div>
        </div>
      )}

      <FunnelEntryModal
        open={entryOpen}
        onOpenChange={setEntryOpen}
        projectId={projectId}
        existing={snapshot}
        onSaved={(s) => setSnapshot(s)}
      />
    </PremiumPanel>
  );
}
