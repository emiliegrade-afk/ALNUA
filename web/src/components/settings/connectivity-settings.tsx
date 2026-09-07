"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Plug, Save, Wifi } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { hubFetch } from "@/lib/hub-fetch";

interface ConnectivityConfig {
  enabled: boolean;
  fallback_on_credit: boolean;
  base_url: string;
  model: string;
  api_key_set: boolean;
  available: boolean;
}

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full border transition ${
        checked
          ? "border-copper/40 bg-copper/30"
          : "border-copper/15 bg-obsidian-deep/60"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-ivory transition ${
          checked ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

export function ConnectivitySettings() {
  const [cfg, setCfg] = useState<ConnectivityConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [apiKey, setApiKey] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await hubFetch<ConnectivityConfig>("/settings/llm-connectivity");
      setCfg(data);
    } catch {
      toast.error("Impossible de charger la connectivité IA.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function save() {
    if (!cfg) return;
    setSaving(true);
    try {
      await hubFetch("/settings/llm-connectivity", {
        method: "POST",
        body: JSON.stringify({ ...cfg, api_key: apiKey }),
      });
      toast.success("Connectivité IA enregistrée.");
      setApiKey("");
      void load();
    } catch {
      toast.error("Erreur lors de l'enregistrement.");
    } finally {
      setSaving(false);
    }
  }

  async function test() {
    setTesting(true);
    try {
      const res = await hubFetch<{ ok: boolean; latency_ms?: number; error?: string }>(
        "/settings/llm-connectivity/test",
        { method: "POST" }
      );
      if (res.ok) {
        toast.success(`Modèle local joignable (${res.latency_ms ?? "?"} ms).`);
      } else {
        toast.error(res.error ?? "Modèle local injoignable.");
      }
    } catch {
      toast.error("Test impossible.");
    } finally {
      setTesting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-copper/50" />
      </div>
    );
  }

  if (!cfg) return null;

  return (
    <section className="rounded-xl border border-copper/10 bg-obsidian-deep/40 p-4">
      <div className="mb-1 flex items-center gap-2">
        <Plug className="h-4 w-4 text-copper" />
        <h2 className="text-lg font-medium text-ivory/90">Connectivité IA</h2>
      </div>
      <p className="mb-4 text-xs text-titanium/60">
        OpenRouter est le fournisseur principal. Active le{" "}
        <span className="text-copper">modèle local</span> et la bascule automatique pour
        continuer quand les crédits OpenRouter sont épuisés (HTTP 402).
      </p>

      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg border border-copper/10 bg-obsidian/40 px-3 py-2.5">
          <div>
            <p className="text-sm text-ivory/85">Modèle local activé</p>
            <p className="text-[11px] text-titanium/50">
              Ollama, LM Studio ou vLLM (endpoint OpenAI-compatible)
            </p>
          </div>
          <Toggle checked={cfg.enabled} onChange={(v) => setCfg({ ...cfg, enabled: v })} />
        </div>

        <div className="flex items-center justify-between rounded-lg border border-copper/10 bg-obsidian/40 px-3 py-2.5">
          <div>
            <p className="text-sm text-ivory/85">Bascule automatique si plus de crédit</p>
            <p className="text-[11px] text-titanium/50">
              Réutilise le modèle local quand OpenRouter renvoie 402
            </p>
          </div>
          <Toggle
            checked={cfg.fallback_on_credit}
            onChange={(v) => setCfg({ ...cfg, fallback_on_credit: v })}
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-titanium/70">
              URL du modèle local
            </span>
            <input
              value={cfg.base_url}
              onChange={(e) => setCfg({ ...cfg, base_url: e.target.value })}
              placeholder="http://localhost:11434/v1"
              className="w-full rounded-lg border border-copper/15 bg-obsidian-deep/50 px-3 py-2 text-sm text-ivory/85 outline-none transition focus:border-copper/40"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-titanium/70">
              Nom du modèle
            </span>
            <input
              value={cfg.model}
              onChange={(e) => setCfg({ ...cfg, model: e.target.value })}
              placeholder="qwen2.5:7b-instruct-q4_K_M"
              className="w-full rounded-lg border border-copper/15 bg-obsidian-deep/50 px-3 py-2 text-sm text-ivory/85 outline-none transition focus:border-copper/40"
            />
          </label>
        </div>

        <label className="block">
          <span className="mb-1 block text-xs font-medium text-titanium/70">
            Clé API (optionnel — {cfg.api_key_set ? "définie, laisser vide pour conserver" : "vide pour Ollama"})
          </span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={cfg.api_key_set ? "•••••••• (inchangée)" : "laisser vide pour Ollama"}
            className="w-full rounded-lg border border-copper/15 bg-obsidian-deep/50 px-3 py-2 text-sm text-ivory/85 outline-none transition focus:border-copper/40"
          />
        </label>

        <div className="flex flex-wrap items-center gap-2 pt-1">
          <Button
            size="sm"
            onClick={() => void save()}
            disabled={saving}
            className="bg-copper text-obsidian hover:bg-copper/90"
          >
            {saving ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="mr-1.5 h-3.5 w-3.5" />
            )}
            Enregistrer
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => void test()}
            disabled={testing || !cfg.enabled}
            className="border-copper/15 text-titanium/70"
          >
            {testing ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Wifi className="mr-1.5 h-3.5 w-3.5" />
            )}
            Tester la connexion
          </Button>
          {cfg.available && (
            <span className="text-[11px] font-medium text-emerald-400/80">Connecté</span>
          )}
        </div>
      </div>
    </section>
  );
}
