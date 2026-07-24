"use client";

import { useEffect, useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import {
  deleteManualCost,
  fetchCombinedCosts,
  recordManualCost,
  type CombinedCostsReport,
} from "@/lib/costs-api";

export function ApiCostsCard() {
  const [report, setReport] = useState<CombinedCostsReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [source, setSource] = useState("");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setReport(await fetchCombinedCosts());
    } catch {
      setReport(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleAdd() {
    const amountUsd = parseFloat(amount);
    if (!source.trim() || !amountUsd || amountUsd <= 0) return;
    setSaving(true);
    try {
      await recordManualCost(source.trim(), amountUsd, note.trim());
      toast.success("Coût enregistré.");
      setSource("");
      setAmount("");
      setNote("");
      setFormOpen(false);
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteManualCost(id);
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  }

  if (loading && !report) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-copper/10 bg-obsidian-2/40 p-4 text-sm text-titanium/60">
        <Loader2 className="h-4 w-4 animate-spin" />
        Chargement des coûts API…
      </div>
    );
  }

  if (!report) return null;

  const eleven = report.elevenlabs;

  return (
    <section className="space-y-3 rounded-xl border border-copper/10 bg-obsidian-2/40 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-ivory">
          Coûts API — 30 derniers jours
        </h2>
        <span className="font-mono text-lg font-semibold text-copper">
          ${report.total_usd_estimate.toFixed(2)}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
          <p className="text-[10px] uppercase tracking-wider text-titanium/50">LLM (OpenRouter)</p>
          <p className="mt-1 font-mono text-lg text-ivory/90">
            ${report.llm.total_cost_usd.toFixed(2)}
          </p>
          <p className="text-[11px] text-titanium/45">{report.llm.total_calls} appels</p>
        </div>

        <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
          <p className="text-[10px] uppercase tracking-wider text-titanium/50">ElevenLabs</p>
          {!eleven.configured ? (
            <p className="mt-1 text-xs text-titanium/50">Clé API non configurée</p>
          ) : !eleven.reachable ? (
            <p className="mt-1 text-xs text-amber-400/80">{eleven.message}</p>
          ) : (
            <>
              <p className="mt-1 font-mono text-lg text-ivory/90">
                {eleven.pct_used}%
                <span className="ml-1 text-xs font-normal text-titanium/50">quota</span>
              </p>
              <p className="text-[11px] text-titanium/45">
                {eleven.character_count?.toLocaleString("fr-FR")} /{" "}
                {eleven.character_limit?.toLocaleString("fr-FR")} caractères
                {eleven.estimated_cost_this_period_usd != null
                  ? ` · ~$${eleven.estimated_cost_this_period_usd.toFixed(2)}`
                  : ""}
              </p>
            </>
          )}
        </div>

        <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
          <p className="text-[10px] uppercase tracking-wider text-titanium/50">
            Hébergeur / manuel
          </p>
          <p className="mt-1 font-mono text-lg text-ivory/90">
            ${report.manual.total_usd.toFixed(2)}
          </p>
          <p className="text-[11px] text-titanium/45">
            {report.manual.entries.length} entrée(s)
          </p>
        </div>
      </div>

      {report.manual.entries.length > 0 ? (
        <ul className="space-y-1">
          {report.manual.entries.map((e) => (
            <li
              key={e.id}
              className="flex items-center justify-between gap-2 rounded-lg bg-white/[0.02] px-3 py-1.5 text-xs"
            >
              <span className="text-ivory/80">
                {e.source} <span className="text-titanium/40">· {e.period}</span>
                {e.note ? <span className="text-titanium/40"> — {e.note}</span> : null}
              </span>
              <span className="flex items-center gap-2">
                <span className="font-mono text-titanium/70">${e.amount_usd.toFixed(2)}</span>
                <button
                  type="button"
                  onClick={() => void handleDelete(e.id)}
                  aria-label="Supprimer cette entrée"
                  className="text-titanium/40 hover:text-red-400"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </span>
            </li>
          ))}
        </ul>
      ) : null}

      {formOpen ? (
        <div className="space-y-2 rounded-lg border border-copper/15 bg-obsidian/60 p-3">
          <div className="grid gap-2 sm:grid-cols-2">
            <input
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="Source (ex: hosting_railway, domaine…)"
              className="rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none placeholder:text-titanium/40"
            />
            <input
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              type="number"
              step="0.01"
              placeholder="Montant USD"
              className="rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none placeholder:text-titanium/40"
            />
          </div>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Note (optionnelle)"
            className="w-full rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none placeholder:text-titanium/40"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setFormOpen(false)}
              className="rounded-lg px-3 py-1.5 text-xs text-titanium/60 hover:text-ivory"
            >
              Annuler
            </button>
            <button
              type="button"
              onClick={() => void handleAdd()}
              disabled={saving || !source.trim() || !amount}
              className="flex items-center gap-1.5 rounded-lg bg-copper px-3 py-1.5 text-xs font-medium text-obsidian hover:bg-copper/90 disabled:opacity-50"
            >
              {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
              Enregistrer
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setFormOpen(true)}
          className="flex items-center gap-1.5 text-xs text-titanium/60 hover:text-copper"
        >
          <Plus className="h-3.5 w-3.5" />
          Ajouter un coût (hébergeur, domaine…)
        </button>
      )}
    </section>
  );
}
