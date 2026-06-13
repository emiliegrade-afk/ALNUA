"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, RefreshCw, RotateCcw, Check, ChevronDown } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ModelGuideCard } from "@/components/settings/model-guide-card";
import { hubFetch } from "@/lib/hub-fetch";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AgentModelConfig {
  agent_id: string;
  tier: "premium" | "standard" | "fast";
  configured: string;  // "auto" or model name
  resolved: string;    // effective model
  label: string;
}

interface AvailableModel {
  label: string;
  tier: "premium" | "standard" | "fast";
  region?: "cn" | "west";
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  return hubFetch<T>(path, options);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TIER_COLORS: Record<string, string> = {
  premium:  "border-amber-500/30 bg-amber-500/8 text-amber-400",
  standard: "border-copper/30 bg-copper/8 text-copper",
  fast:     "border-white/15 bg-white/5 text-titanium/70",
};

const TIER_LABELS: Record<string, string> = {
  premium:  "Premium",
  standard: "Standard",
  fast:     "Rapide",
};

const AGENT_LABELS: Record<string, string> = {
  coo:           "COO — Chef d'orchestre",
  spec:          "Spec — Rédacteur de specs",
  brainstorm:    "Brainstorm — Idéation",
  game_director: "Game Director — Naïa",
  rnd_agent:     "R&D — Recherche autonome",
  qa:            "QA — Tests & qualité",
  dev_app:       "Dev App — NUAWAY",
  dev_gaming:    "Dev Gaming — Naïa",
  marketing:     "Marketing",
  hardware:      "Hardware",
  embedded_dev:  "Embedded Dev",
  content:       "Content — Rédaction",
  pm:               "PM — Gestion de projet",
  accounting:       "Comptabilité",
  secretary:        "Secrétaire de Direction",
  dev_backend:      "Dev Backend & API",
  level_designer:   "Level & Narrative Designer",
  controller:       "Contrôleur de Gestion",
  analyst_business: "Business Analyst",
  analyst_data:     "Data Analyst — BI",
};

const REGION_LABELS: Record<string, string> = {
  cn: "🇨🇳 Chine",
  west: "🌍 Occidental",
};

// ---------------------------------------------------------------------------
// ModelSelector
// ---------------------------------------------------------------------------

function ModelSelector({
  agentId,
  current,
  availableModels,
  onSave,
}: {
  agentId: string;
  current: string;
  availableModels: Record<string, AvailableModel>;
  onSave: (agentId: string, model: string) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  async function select(model: string) {
    setOpen(false);
    setSaving(true);
    await onSave(agentId, model);
    setSaving(false);
  }

  const tiers = ["premium", "standard", "fast"] as const;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-ivory/80 transition hover:border-white/20"
      >
        <span className="truncate">
          {current === "auto"
            ? "Auto"
            : availableModels[current]?.label ?? current}
        </span>
        {saving ? (
          <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-copper" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-titanium/40" />
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-1 max-h-96 w-80 overflow-y-auto rounded-xl border border-white/10 bg-obsidian shadow-xl">
            {/* Auto */}
            <button
              onClick={() => select("auto")}
              className="flex w-full items-center justify-between px-3 py-2.5 text-sm text-titanium/80 transition hover:bg-white/5"
            >
              <span>Auto (recommandé)</span>
              {current === "auto" && <Check className="h-3.5 w-3.5 text-copper" />}
            </button>
            <div className="border-t border-white/5" />

            {tiers.map((tier) => {
              const models = Object.entries(availableModels).filter(
                ([, v]) => v.tier === tier
              );
              if (!models.length) return null;
              const regions = ["cn", "west"] as const;
              return (
                <div key={tier}>
                  <p className="sticky top-0 z-10 bg-obsidian px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-titanium/40">
                    {TIER_LABELS[tier]}
                  </p>
                  {regions.map((region) => {
                    const regionModels = models.filter(([, v]) => (v.region ?? "west") === region);
                    if (!regionModels.length) return null;
                    return (
                      <div key={region}>
                        <p className="px-3 py-1 text-[9px] font-medium uppercase tracking-wider text-titanium/30">
                          {REGION_LABELS[region]}
                        </p>
                        {regionModels.map(([id, info]) => (
                          <button
                            key={id}
                            onClick={() => select(id)}
                            className="flex w-full items-center justify-between px-3 py-2 text-sm text-ivory/80 transition hover:bg-white/5"
                          >
                            <span className="truncate pr-2">{info.label}</span>
                            {current === id && <Check className="h-3.5 w-3.5 shrink-0 text-copper" />}
                          </button>
                        ))}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main view
// ---------------------------------------------------------------------------

export function ModelSettingsView() {
  const [agents, setAgents] = useState<AgentModelConfig[]>([]);
  const [availableModels, setAvailableModels] = useState<Record<string, AvailableModel>>({});
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [agentsData, modelsData] = await Promise.all([
        apiFetch<AgentModelConfig[]>("/settings/models"),
        apiFetch<{ models: Record<string, AvailableModel> }>("/settings/models/available"),
      ]);
      setAgents(agentsData);
      setAvailableModels(modelsData.models);
    } catch {
      toast.error("Impossible de charger les paramètres modèles.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleSave(agentId: string, model: string) {
    try {
      await apiFetch("/settings/models", {
        method: "POST",
        body: JSON.stringify({ agent_id: agentId, model }),
      });
      setAgents((prev) =>
        prev.map((a) =>
          a.agent_id === agentId
            ? {
                ...a,
                configured: model,
                resolved: model === "auto"
                  ? a.resolved  // will refresh
                  : model,
                label: availableModels[model]?.label ?? model,
              }
            : a
        )
      );
      toast.success(`${AGENT_LABELS[agentId] ?? agentId} → ${model === "auto" ? "Auto" : availableModels[model]?.label ?? model}`);
      load(); // refresh resolved values
    } catch {
      toast.error("Erreur lors de la mise à jour.");
    }
  }

  async function handleResetAll() {
    setResetting(true);
    try {
      await apiFetch("/settings/models/reset", { method: "POST" });
      toast.success("Tous les agents repassés en mode Auto.");
      load();
    } catch {
      toast.error("Erreur lors du reset.");
    } finally {
      setResetting(false);
    }
  }

  const tierGroups = ["premium", "standard", "fast"] as const;

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium text-ivory/90">Modèles LLM par agent</h2>
          <p className="mt-0.5 text-xs text-titanium/60">
            Mode <span className="text-copper">Auto</span> = modèle choisi selon le tier de l'agent.
            Tu peux forcer un modèle spécifique par agent.
          </p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={load} className="border-white/10 text-titanium/70">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleResetAll}
            disabled={resetting}
            className="border-white/10 text-titanium/70 hover:text-ivory/80"
          >
            {resetting ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <RotateCcw className="mr-1.5 h-3.5 w-3.5" />}
            Tout passer en Auto
          </Button>
        </div>
      </div>

      {/* Guide */}
      <ModelGuideCard />

      {/* Tier legend */}
      <div className="flex flex-wrap gap-3 text-xs">
        {tierGroups.map((tier) => (
          <span key={tier} className={`rounded-full border px-3 py-1 ${TIER_COLORS[tier]}`}>
            <span className="font-semibold">{TIER_LABELS[tier]}</span>
            {tier === "premium" && " — raisonnement complexe, créativité"}
            {tier === "standard" && " — code, analyse, contenu"}
            {tier === "fast" && " — tâches simples, résumés"}
          </span>
        ))}
      </div>

      {/* Agent list grouped by tier */}
      {tierGroups.map((tier) => {
        const tierAgents = agents.filter((a) => a.tier === tier);
        if (!tierAgents.length) return null;
        return (
          <div key={tier}>
            <h3 className={`mb-3 text-xs font-semibold uppercase tracking-widest ${TIER_COLORS[tier].split(" ").pop()}`}>
              {TIER_LABELS[tier]}
            </h3>
            <div className="grid gap-2 sm:grid-cols-2">
              {tierAgents.map((agent) => (
                <div
                  key={agent.agent_id}
                  className="flex items-center gap-3 rounded-xl border border-white/8 bg-white/[0.02] p-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-ivory/85">
                      {AGENT_LABELS[agent.agent_id] ?? agent.agent_id}
                    </p>
                    {agent.configured !== "auto" && (
                      <p className="mt-0.5 text-[10px] text-titanium/40">
                        Résolu : {agent.label}
                      </p>
                    )}
                    {agent.configured === "auto" && (
                      <p className="mt-0.5 text-[10px] text-titanium/40">
                        Auto → {agent.label}
                      </p>
                    )}
                  </div>
                  <div className="w-44 shrink-0">
                    <ModelSelector
                      agentId={agent.agent_id}
                      current={agent.configured}
                      availableModels={availableModels}
                      onSave={handleSave}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
