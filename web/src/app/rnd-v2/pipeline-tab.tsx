"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchRndIdeas, type RndIdea } from "@/lib/rnd";
import { C } from "../app-v2/shared";
import { DossierDetailView } from "./dossier-detail-view";

/* Innovation Pipeline (Phase 23, ROADMAP.md) — remplace l'ancien Centre R&D
   ("chat + liste") par des cartes score/verdict. Aucune donnée fabriquée :
   score/verdict/sous-scores viennent tels quels de `rnd_ideas`
   (services/rnd_schemas.py::RndIdeaOut, déjà calculés par rnd_center.py) —
   pas de nouveau endpoint, `fetchRndIdeas` existait déjà. */

const VERDICT_META: Record<string, { label: string; color: string; bg: string; border: string }> = {
  GO: { label: "GO", color: "#2DD4BF", bg: "rgba(45,212,191,.12)", border: "rgba(45,212,191,.3)" },
  MAYBE: { label: "MAYBE", color: "#E0A95C", bg: "rgba(224,169,92,.12)", border: "rgba(224,169,92,.3)" },
  NO: { label: "NO", color: "#f87171", bg: "rgba(248,113,113,.12)", border: "rgba(248,113,113,.3)" },
};

const FILTERS = ["Toutes", "GO", "MAYBE", "NO"] as const;
type Filter = (typeof FILTERS)[number];

function ScoreTile({ label, value }: { label: string; value?: number }) {
  return (
    <div className="rounded-md border px-1.5 py-1 text-center" style={{ borderColor: C.lineSoft, background: "rgba(22,17,13,.4)" }}>
      <p className="text-[11px] font-semibold" style={{ color: value == null ? C.faint : C.ivory }}>
        {value ?? "—"}
        <span className="text-[8px] font-normal" style={{ color: C.faint }}>
          /10
        </span>
      </p>
      <p className="text-[7.5px] uppercase tracking-wide" style={{ color: C.faint }}>
        {label}
      </p>
    </div>
  );
}

function IdeaCard({ idea, onOpen }: { idea: RndIdea; onOpen: () => void }) {
  const verdict = idea.verdict ? VERDICT_META[idea.verdict] : null;
  return (
    <button
      type="button"
      onClick={onOpen}
      className="animate-rnd-card-breathe flex flex-col gap-2.5 rounded-xl border p-3.5 text-left transition-transform hover:-translate-y-0.5"
      style={{ borderColor: verdict?.border ?? C.line, background: "#000000" }}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0 flex-1 truncate text-[13.5px] font-semibold" style={{ color: C.ivory }}>
          {idea.title}
        </span>
        {verdict ? (
          <span
            className="shrink-0 rounded-full border px-2 py-0.5 text-[9px] font-semibold"
            style={{ borderColor: verdict.border, background: verdict.bg, color: verdict.color }}
          >
            {verdict.label}
          </span>
        ) : (
          <span className="shrink-0 rounded-full border px-2 py-0.5 text-[9px]" style={{ borderColor: C.lineSoft, color: C.faint }}>
            En attente
          </span>
        )}
      </div>

      <p className="line-clamp-2 min-h-[26px] text-[10.5px]" style={{ color: C.dim }}>
        {idea.description || "—"}
      </p>

      <div className="flex items-center gap-2.5">
        <div className="relative h-9 w-9 shrink-0">
          <svg width="36" height="36" viewBox="0 0 36 36">
            <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(224,155,106,.15)" strokeWidth="3.5" />
            {idea.score != null ? (
              <circle
                cx="18"
                cy="18"
                r="15"
                fill="none"
                stroke={C.copper}
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeDasharray={`${((idea.score / 100) * 2 * Math.PI * 15).toFixed(1)} ${(2 * Math.PI * 15).toFixed(1)}`}
                transform="rotate(-90 18 18)"
              />
            ) : null}
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-[10px] font-semibold" style={{ color: C.ivory }}>
            {idea.score ?? "—"}
          </span>
        </div>
        <div className="grid flex-1 grid-cols-3 gap-1">
          <ScoreTile label="Marché" value={idea.market_score} />
          <ScoreTile label="Tech" value={idea.feasibility_score} />
          <ScoreTile label="Business" value={idea.vision_score} />
        </div>
      </div>

      <div className="flex items-center justify-between border-t pt-2 text-[9px]" style={{ borderColor: C.lineSoft, color: C.faint }}>
        <span className="truncate">{idea.domain || "—"}</span>
        <span className="shrink-0">{idea.dossier_id ? "Dossier ouvert" : "Pas encore de dossier"}</span>
      </div>
    </button>
  );
}

export function PipelineTab() {
  const [ideas, setIdeas] = useState<RndIdea[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("Toutes");
  const [openIdea, setOpenIdea] = useState<RndIdea | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    // `false` = pipeline complet, pas seulement l'inbox (ideas non encore triées).
    fetchRndIdeas(undefined, false)
      .then((all) => {
        if (!cancelled) setIdeas(all);
      })
      .catch(() => {
        if (!cancelled) setIdeas([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const sorted = [...ideas].sort((a, b) => (b.score ?? -1) - (a.score ?? -1));
    if (filter === "Toutes") return sorted;
    return sorted.filter((i) => i.verdict === filter);
  }, [ideas, filter]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          INNOVATION PIPELINE — {ideas.length} idée{ideas.length !== 1 ? "s" : ""}
        </p>
        <div className="flex items-center gap-1.5">
          {FILTERS.map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className="rounded-full border px-2.5 py-1 text-[10px]"
              style={
                filter === f
                  ? { borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.12)", color: C.copperLight }
                  : { borderColor: C.lineSoft, color: C.faint }
              }
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex min-h-[200px] flex-1 items-center justify-center rounded-xl border text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
          Chargement du pipeline…
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex min-h-[200px] flex-1 items-center justify-center rounded-xl border text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
          {ideas.length === 0 ? "Aucune idée dans le pipeline pour le moment." : "Aucune idée pour ce filtre."}
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-3">
          {filtered.map((idea) => (
            <IdeaCard key={idea.id} idea={idea} onOpen={() => setOpenIdea(idea)} />
          ))}
        </div>
      )}

      <DossierDetailView
        idea={openIdea}
        onClose={() => setOpenIdea(null)}
        onIdeaUpdated={(updated) => setIdeas((prev) => prev.map((i) => (i.id === updated.id ? updated : i)))}
        onIdeaArchived={(ideaId) => setIdeas((prev) => prev.filter((i) => i.id !== ideaId))}
      />
    </div>
  );
}
