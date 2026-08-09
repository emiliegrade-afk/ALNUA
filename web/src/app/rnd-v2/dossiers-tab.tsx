"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchRndDossierTableView, type RndDossierTableRow } from "@/lib/rnd-dossier";
import type { RndIdea } from "@/lib/rnd";
import { C } from "../app-v2/shared";
import { DossierDetailView } from "./dossier-detail-view";

/* Dossiers (Phase 27, ROADMAP.md) — vue table façon Notion premium.
   Colonnes du plan (Résumé/État/Dernière MAJ/Score/Agents/Votes/Documents/
   Concurrence/Études/Prototype/Décision) : "Concurrence" et "Études"
   fusionnées en une seule colonne "Marché" — les deux proviennent de la
   même section `market` du dossier, un seul texte réel, pas deux valeurs
   fabriquées à partir d'une seule source. Toutes les données viennent de
   GET /rnd/dossiers/table-view (services/rnd_dossier_table.py), qui
   pré-joint idée/vote Conseil/documents/section marché côté serveur.

   "Ouvrir" rouvre `DossierDetailView` (Phase 23) — le même overlay rapide
   déjà utilisé par le Pipeline — plutôt que de renvoyer vers l'ancienne
   page `/rd` : signalé par Emilie comme une mauvaise expérience (page
   lourde, popup peu clair, ~10s de chargement pour une simple ouverture).
   `DossierDetailView` attend un objet `RndIdea` ; reconstruit ici à partir
   de la ligne du tableau (`rowToIdea`) plutôt que de refaire un aller-retour
   réseau — toutes les données nécessaires (score, sous-scores, verdict,
   idea_legacy_id) sont déjà dans la ligne. */

function rowToIdea(r: RndDossierTableRow): RndIdea {
  return {
    id: r.idea_legacy_id ?? r.id,
    title: r.title,
    description: r.tagline ?? r.title,
    domain: r.domain,
    score: r.score ?? undefined,
    verdict: r.verdict ?? undefined,
    market_score: r.market_score ?? undefined,
    feasibility_score: r.feasibility_score ?? undefined,
    vision_score: r.vision_score ?? undefined,
    incubator_stage: (r.incubator_stage as RndIdea["incubator_stage"]) ?? undefined,
    dossier_id: r.id,
  };
}

const STATUS_LABEL: Record<string, string> = {
  draft: "Brouillon",
  committee_active: "Comité actif",
  partial_validated: "Partiel. validé",
  ready_for_ceo: "Prêt CEO",
  ceo_approved: "Approuvé CEO",
  ceo_rejected: "Rejeté CEO",
  in_conception: "En conception",
  published: "Publié",
  archived: "Archivé",
};

const CEO_STATUS_META: Record<string, { label: string; color: string }> = {
  pending: { label: "En attente", color: C.faint },
  approved: { label: "Approuvé", color: "#7FC98C" },
  rejected: { label: "Rejeté", color: "#f87171" },
  pivot_requested: { label: "Pivot demandé", color: "#E0A95C" },
};

const VERDICT_COLOR: Record<string, string> = {
  GO: "#7FC98C",
  MAYBE: "#E0A95C",
  NO: "#f87171",
};

function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "2-digit" });
  } catch {
    return "—";
  }
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th
      className="sticky top-0 z-10 whitespace-nowrap border-b px-3 py-2 text-left text-[9px] font-medium tracking-[1.2px]"
      style={{ borderColor: C.lineSoft, background: "#100D0B", color: C.faint }}
    >
      {children}
    </th>
  );
}

function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <td className={`border-b px-3 py-2.5 align-top text-[11px] ${className}`} style={{ borderColor: C.lineSoft, color: C.warm }}>
      {children}
    </td>
  );
}

export function DossiersTab() {
  const [rows, setRows] = useState<RndDossierTableRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("Toutes");
  const [openIdea, setOpenIdea] = useState<RndIdea | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchRndDossierTableView({ limit: 100 })
      .then((data) => {
        if (!cancelled) setRows(data);
      })
      .catch(() => {
        if (!cancelled) setRows([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const statuses = useMemo(() => Array.from(new Set(rows.map((r) => r.status))), [rows]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return rows.filter((r) => {
      if (statusFilter !== "Toutes" && r.status !== statusFilter) return false;
      if (!q) return true;
      return r.title.toLowerCase().includes(q) || (r.tagline ?? "").toLowerCase().includes(q);
    });
  }, [rows, search, statusFilter]);

  if (loading) {
    return (
      <div className="flex min-h-[200px] flex-1 items-center justify-center rounded-xl border text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
        Chargement des dossiers…
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden pb-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          DOSSIERS — {rows.length} dossier{rows.length !== 1 ? "s" : ""}
        </p>
        <div className="flex items-center gap-1.5">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher un dossier…"
            className="w-[200px] rounded-lg border bg-transparent px-2.5 py-1 text-[10.5px] outline-none"
            style={{ borderColor: C.lineSoft, color: C.ivory }}
          />
          <button
            type="button"
            onClick={() => setStatusFilter("Toutes")}
            className="rounded-full border px-2.5 py-1 text-[10px]"
            style={
              statusFilter === "Toutes"
                ? { borderColor: "rgba(192,138,114,.45)", background: "rgba(192,138,114,.12)", color: C.copperLight }
                : { borderColor: C.lineSoft, color: C.faint }
            }
          >
            Toutes
          </button>
          {statuses.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStatusFilter(s)}
              className="rounded-full border px-2.5 py-1 text-[10px]"
              style={
                statusFilter === s
                  ? { borderColor: "rgba(192,138,114,.45)", background: "rgba(192,138,114,.12)", color: C.copperLight }
                  : { borderColor: C.lineSoft, color: C.faint }
              }
            >
              {STATUS_LABEL[s] ?? s}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="flex min-h-[200px] flex-1 items-center justify-center rounded-xl border text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
          {rows.length === 0 ? "Aucun dossier R&D pour le moment." : "Aucun dossier pour ce filtre."}
        </div>
      ) : (
        <div className="alnua-scroll min-h-0 flex-1 overflow-auto rounded-xl border" style={{ borderColor: C.line }}>
          <table className="w-full min-w-[1180px] border-collapse">
            <thead>
              <tr>
                <Th>Résumé</Th>
                <Th>État</Th>
                <Th>Dernière MAJ</Th>
                <Th>Score</Th>
                <Th>Agents</Th>
                <Th>Votes</Th>
                <Th>Documents</Th>
                <Th>Marché</Th>
                <Th>Prototype</Th>
                <Th>Décision</Th>
                <Th>&nbsp;</Th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const ceoMeta = CEO_STATUS_META[r.ceo_status] ?? { label: r.ceo_status, color: C.faint };
                return (
                  <tr key={r.id} className="transition-colors hover:bg-obsidian-deep/40">
                    <Td className="min-w-[220px] max-w-[260px]">
                      <p className="truncate font-semibold" style={{ color: C.ivory }}>
                        {r.title}
                      </p>
                      {r.tagline ? (
                        <p className="mt-0.5 line-clamp-2 text-[9.5px]" style={{ color: C.dim }}>
                          {r.tagline}
                        </p>
                      ) : null}
                    </Td>
                    <Td>
                      <span className="whitespace-nowrap rounded-full border px-2 py-0.5 text-[9px]" style={{ borderColor: C.lineSoft, color: C.warm }}>
                        {STATUS_LABEL[r.status] ?? r.status}
                      </span>
                    </Td>
                    <Td className="whitespace-nowrap">{formatDate(r.updated_at)}</Td>
                    <Td className="whitespace-nowrap">
                      {r.score != null ? (
                        <span>
                          <span className="font-semibold" style={{ color: C.ivory }}>
                            {r.score}
                          </span>
                          <span style={{ color: C.faint }}>/100</span>
                          {r.verdict ? (
                            <span className="ml-1.5 font-semibold" style={{ color: VERDICT_COLOR[r.verdict] }}>
                              {r.verdict}
                            </span>
                          ) : null}
                        </span>
                      ) : (
                        <span style={{ color: C.faint }}>—</span>
                      )}
                    </Td>
                    <Td className="whitespace-nowrap">
                      {r.agents_count > 0 ? r.agents_count : <span style={{ color: C.faint }}>—</span>}
                    </Td>
                    <Td className="whitespace-nowrap">
                      {r.votes ? (
                        <span>
                          <span className="font-semibold" style={{ color: VERDICT_COLOR[r.votes.verdict] }}>
                            {r.votes.verdict}
                          </span>
                          <span className="ml-1" style={{ color: C.faint }}>
                            {r.votes.consensus_pct}%
                          </span>
                        </span>
                      ) : (
                        <span style={{ color: C.faint }}>—</span>
                      )}
                    </Td>
                    <Td className="whitespace-nowrap">
                      {r.documents_count > 0 ? r.documents_count : <span style={{ color: C.faint }}>—</span>}
                    </Td>
                    <Td className="min-w-[200px] max-w-[240px]">
                      {r.market_excerpt ? (
                        <p className="line-clamp-2 text-[10px]" style={{ color: C.dim }} title={r.market_excerpt}>
                          {r.market_excerpt}
                        </p>
                      ) : (
                        <span style={{ color: C.faint }}>—</span>
                      )}
                    </Td>
                    <Td className="whitespace-nowrap">{r.prototype_label ?? <span style={{ color: C.faint }}>—</span>}</Td>
                    <Td className="min-w-[140px]">
                      <span className="font-medium" style={{ color: ceoMeta.color }}>
                        {ceoMeta.label}
                      </span>
                      {r.ceo_note ? (
                        <p className="mt-0.5 line-clamp-2 text-[9.5px]" style={{ color: C.dim }}>
                          {r.ceo_note}
                        </p>
                      ) : null}
                    </Td>
                    <Td className="whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => setOpenIdea(rowToIdea(r))}
                        className="rounded-lg border px-2 py-1 text-[9.5px]"
                        style={{ borderColor: "rgba(192,138,114,.4)", color: C.copperLight }}
                      >
                        Ouvrir
                      </button>
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <DossierDetailView
        idea={openIdea}
        onClose={() => setOpenIdea(null)}
        onIdeaArchived={(ideaId) => setRows((prev) => prev.filter((r) => r.idea_legacy_id !== ideaId))}
      />
    </div>
  );
}
