"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
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
  configured: string;
  resolved: string;
  label: string;
  display_name: string;
  role_label: string;
  department: string;
  room?: string;
  codes?: boolean;
  coding_model?: string | null;
}

interface AvailableModel {
  label: string;
  tier: "premium" | "standard" | "fast";
  category: string;
  region?: "cn" | "west";
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  return hubFetch<T>(path, options);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TIER_COLORS: Record<string, string> = {
  premium: "border-amber-500/30 bg-amber-500/8 text-amber-400",
  standard: "border-copper/30 bg-copper/8 text-copper",
  fast: "border-white/15 bg-white/5 text-titanium/70",
};

const TIER_LABELS: Record<string, string> = {
  premium: "Premium",
  standard: "Standard",
  fast: "Rapide",
};

const CATEGORY_HINTS: Record<string, string> = {
  reasoning: "Décisions, stratégie, analyse profonde",
  code: "Dev, specs techniques, agents code",
  chat: "Rédaction, support, contenu général",
  fast: "Triage, résumés, tâches simples",
  uncensored: "Créatif, brainstorming, peu de refus",
};

// ---------------------------------------------------------------------------
// ModelSelector — groupé par usage (code / chat / reasoning…)
// ---------------------------------------------------------------------------

function ModelSelector({
  agentId,
  current,
  availableModels,
  categories,
  categoryOrder,
  onSave,
}: {
  agentId: string;
  current: string;
  availableModels: Record<string, AvailableModel>;
  categories: Record<string, string>;
  categoryOrder: string[];
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

  return (
    <div className="relative">
      <button
        type="button"
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
          <div className="absolute right-0 z-20 mt-1 max-h-[28rem] w-80 overflow-y-auto rounded-xl border border-white/10 bg-obsidian shadow-xl">
            <button
              type="button"
              onClick={() => select("auto")}
              className="flex w-full items-center justify-between px-3 py-2.5 text-sm text-titanium/80 transition hover:bg-white/5"
            >
              <span>Auto (tier agent)</span>
              {current === "auto" && <Check className="h-3.5 w-3.5 text-copper" />}
            </button>
            <div className="border-t border-white/5" />

            {categoryOrder.map((catId) => {
              const models = Object.entries(availableModels).filter(
                ([, v]) => v.category === catId
              );
              if (!models.length) return null;
              return (
                <div key={catId}>
                  <p className="sticky top-0 z-10 bg-obsidian px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-titanium/40">
                    {categories[catId] ?? catId}
                  </p>
                  {CATEGORY_HINTS[catId] && (
                    <p className="px-3 pb-1 text-[9px] text-titanium/30">
                      {CATEGORY_HINTS[catId]}
                    </p>
                  )}
                  {models.map(([id, info]) => (
                    <button
                      key={id}
                      type="button"
                      onClick={() => select(id)}
                      className="flex w-full items-center justify-between px-3 py-2 text-sm text-ivory/80 transition hover:bg-white/5"
                    >
                      <span className="truncate pr-2">{info.label}</span>
                      {current === id && (
                        <Check className="h-3.5 w-3.5 shrink-0 text-copper" />
                      )}
                    </button>
                  ))}
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
  const [categories, setCategories] = useState<Record<string, string>>({});
  const [categoryOrder, setCategoryOrder] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [agentsData, modelsData] = await Promise.all([
        apiFetch<AgentModelConfig[]>("/settings/models"),
        apiFetch<{
          models: Record<string, AvailableModel>;
          categories: Record<string, string>;
          category_order: string[];
        }>("/settings/models/available"),
      ]);
      setAgents(agentsData);
      setAvailableModels(modelsData.models ?? {});
      setCategories(modelsData.categories ?? {});
      setCategoryOrder(
        modelsData.category_order?.length
          ? modelsData.category_order
          : ["reasoning", "code", "chat", "fast", "uncensored"]
      );
    } catch {
      toast.error("Impossible de charger les paramètres modèles.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const agentsByDepartment = useMemo(() => {
    const map = new Map<string, AgentModelConfig[]>();
    for (const agent of agents) {
      const dept = agent.department || "ALNUA";
      const list = map.get(dept) ?? [];
      list.push(agent);
      map.set(dept, list);
    }
    return Array.from(map.entries());
  }, [agents]);

  async function handleSave(agentId: string, model: string) {
    const agent = agents.find((a) => a.agent_id === agentId);
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
                resolved: model === "auto" ? a.resolved : model,
                label: availableModels[model]?.label ?? model,
              }
            : a
        )
      );
      const name = agent?.display_name ?? agentId;
      toast.success(
        `${name} → ${model === "auto" ? "Auto" : availableModels[model]?.label ?? model}`
      );
      load();
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

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium text-ivory/90">Modèles LLM par agent</h2>
          <p className="mt-0.5 text-xs text-titanium/60">
            Chaque agent affiche son <span className="text-copper">nom</span> et son{" "}
            <span className="text-copper">département</span>. Les modèles sont classés par{" "}
            <span className="text-copper">usage</span> (code, chat, raisonnement, non censuré…).
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => void load()}
            className="border-white/10 text-titanium/70"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => void handleResetAll()}
            disabled={resetting}
            className="border-white/10 text-titanium/70 hover:text-ivory/80"
          >
            {resetting ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
            )}
            Tout passer en Auto
          </Button>
        </div>
      </div>

      <ModelGuideCard />

      <div className="flex flex-wrap gap-2 text-xs">
        {categoryOrder.map((catId) => (
          <span
            key={catId}
            className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-titanium/60"
          >
            <span className="font-semibold text-ivory/75">
              {categories[catId] ?? catId}
            </span>
            {CATEGORY_HINTS[catId] ? ` — ${CATEGORY_HINTS[catId]}` : null}
          </span>
        ))}
      </div>

      {agentsByDepartment.map(([department, deptAgents]) => (
        <div key={department}>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-copper/80">
            {department}
          </h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {deptAgents.map((agent) => (
              <div
                key={agent.agent_id}
                className="flex items-center gap-3 rounded-xl border border-white/8 bg-white/[0.02] p-3"
              >
                <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-ivory/90">
                      {agent.display_name || agent.agent_id}
                    <span
                      className={`ml-2 rounded-full border px-1.5 py-0.5 text-[9px] font-medium ${TIER_COLORS[agent.tier]}`}
                    >
                      {TIER_LABELS[agent.tier]}
                    </span>
                    {agent.codes ? (
                      <span className="ml-1.5 rounded bg-copper/15 px-1.5 py-0.5 text-[9px] font-medium text-copper">
                        chat + code
                      </span>
                    ) : null}
                  </p>
                  <p className="mt-0.5 text-[11px] text-titanium/55">
                    {agent.role_label || agent.agent_id}
                  </p>
                  {agent.department ? (
                    <p className="mt-0.5 text-[10px] text-titanium/40">{agent.department}</p>
                  ) : null}
                  <p className="mt-0.5 text-[10px] text-titanium/40">
                    {agent.configured === "auto"
                      ? `Auto → ${agent.label}`
                      : `Résolu : ${agent.label}`}
                  </p>
                </div>
                <div className="w-44 shrink-0">
                  <ModelSelector
                    agentId={agent.agent_id}
                    current={agent.configured}
                    availableModels={availableModels}
                    categories={categories}
                    categoryOrder={categoryOrder}
                    onSave={handleSave}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
