"use client";

import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { CampaignModal } from "@/components/marketing/campaign-modal";
import {
  CAMPAIGN_OBJECTIVE_LABELS,
  CAMPAIGN_PLATFORM_LABELS,
  CAMPAIGN_STATUS_COLORS,
  CAMPAIGN_STATUS_LABELS,
} from "@/components/marketing/campaign.constants";
import { fetchProjects } from "@/lib/api";
import { fetchCampaigns, type Campaign } from "@/lib/marketing-api";
import { formatCurrency } from "@/lib/finances-api";
import type { Project } from "@/lib/types";
import { C, Bar } from "../app-v2/shared";

/* Onglet "Campagnes" — Phase 33, ROADMAP.md. Grille de cartes (pas de Kanban,
   le statut d'une campagne change moins souvent qu'un post). budget_allocated
   vs spent_usd sont tous deux réels (spent_usd = somme des transactions
   transactions.campaign_id côté backend) — aucun ROI/reach affiché, ce sont
   des stubs backend (skills/skill_ads.py::campaign_roi_report) jamais exposés
   ici. */

export function CampagnesTab() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Campaign | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [c, p] = await Promise.all([fetchCampaigns(), fetchProjects()]);
      setCampaigns(c);
      setProjects(p);
    } catch {
      setCampaigns([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function openNew() {
    setEditing(null);
    setModalOpen(true);
  }
  function openEdit(campaign: Campaign) {
    setEditing(campaign);
    setModalOpen(true);
  }

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-1">
      <div className="flex items-center justify-between">
        <p className="text-[11px]" style={{ color: C.dim }}>
          {campaigns.length} campagne{campaigns.length !== 1 ? "s" : ""}
        </p>
        <button
          type="button"
          onClick={openNew}
          className="flex items-center gap-1.5 rounded-[18px] border px-[13px] py-1.5 text-[11.5px]"
          style={{ borderColor: "rgba(192,138,114,.45)", background: "rgba(192,138,114,.08)", color: C.copperLight }}
        >
          <Plus className="h-3.5 w-3.5" /> Nouvelle campagne
        </button>
      </div>

      {loading && campaigns.length === 0 ? (
        <p className="text-center text-[11px]" style={{ color: C.faint }}>
          Chargement des campagnes…
        </p>
      ) : campaigns.length === 0 ? (
        <p className="rounded-xl border border-dashed p-6 text-center text-[10.5px]" style={{ borderColor: C.line, color: C.faint }}>
          Aucune campagne pour l&apos;instant. Crée-la manuellement ou demande à Léo (panneau Console
          Marketing plus bas).
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {campaigns.map((c) => {
            const pct = c.budget_allocated_usd > 0 ? Math.min(100, Math.round((c.spent_usd / c.budget_allocated_usd) * 100)) : 0;
            return (
              <button
                key={c.id}
                type="button"
                onClick={() => openEdit(c)}
                className="flex flex-col gap-2.5 rounded-xl border p-3 text-left transition-colors hover:opacity-90"
                style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="min-w-0 truncate text-[12.5px] font-semibold" style={{ color: C.ivory }}>
                    {c.name}
                  </span>
                  <span
                    className="shrink-0 rounded px-1.5 py-0.5 text-[8.5px]"
                    style={{ background: "rgba(255,255,255,.04)", color: CAMPAIGN_STATUS_COLORS[c.status] }}
                  >
                    {CAMPAIGN_STATUS_LABELS[c.status]}
                  </span>
                </div>
                <div className="flex gap-2 text-[9px]" style={{ color: C.faint }}>
                  <span>{CAMPAIGN_PLATFORM_LABELS[c.platform] ?? c.platform}</span>
                  <span>·</span>
                  <span>{CAMPAIGN_OBJECTIVE_LABELS[c.objective] ?? c.objective}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Bar value={pct} thick={4} />
                  <span className="shrink-0 text-[9.5px]" style={{ color: C.warm }}>
                    {pct}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-[9.5px]" style={{ color: C.dim }}>
                  <span>{formatCurrency(c.spent_usd)} dépensés</span>
                  <span>/ {formatCurrency(c.budget_allocated_usd)}</span>
                </div>
                {c.start_date || c.end_date ? (
                  <p className="text-[9px]" style={{ color: C.faint }}>
                    {c.start_date ?? "—"} → {c.end_date ?? "—"}
                  </p>
                ) : null}
              </button>
            );
          })}
        </div>
      )}

      <CampaignModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        projects={projects}
        campaign={editing}
        onSaved={() => void load()}
      />
    </div>
  );
}
