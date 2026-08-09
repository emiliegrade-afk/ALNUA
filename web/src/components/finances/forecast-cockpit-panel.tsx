"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  fetchCockpitForecast,
  formatCurrency,
  runFinanceForecastLlm,
  type CockpitForecast,
} from "@/lib/finances-api";
import { C } from "@/app/app-v2/shared";

export function ForecastCockpitPanel({ period }: { period: string }) {
  const [data, setData] = useState<CockpitForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [llmBusy, setLlmBusy] = useState(false);
  const [llmNotes, setLlmNotes] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchCockpitForecast(period)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) {
          toast.error(e instanceof Error ? e.message : "Forecast cockpit impossible");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [period]);

  async function runRemi() {
    setLlmBusy(true);
    setLlmNotes(null);
    try {
      const out = await runFinanceForecastLlm({
        period,
        horizon_months: data?.horizon_months ?? 6,
        project: "ALNUA global",
      });
      const llm = out.llm_forecast as Record<string, unknown>;
      const conf = String(llm.confidence ?? "?");
      const be = String(llm.break_even_month ?? "n/a");
      setLlmNotes(`Rémi — confiance ${conf} · break-even ${be}`);
      toast.success("Forecast LLM Rémi prêt");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Forecast LLM échoué");
    } finally {
      setLlmBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-4 text-[11px]" style={{ color: C.dim }}>
        <Loader2 className="h-3.5 w-3.5 animate-spin" /> Forecast cockpit…
      </div>
    );
  }
  if (!data) return null;

  const burn = data.projection.monthly_burn_estimate;
  const runway = data.projection.runway_months_on_envelopes;

  return (
    <section className="rounded-xl border p-3" style={{ borderColor: C.line }}>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-[12px] font-medium" style={{ color: C.ivory }}>
          Forecast cockpit — {data.period}
        </h3>
        <button
          type="button"
          disabled={llmBusy}
          onClick={() => void runRemi()}
          className="rounded-full border px-2.5 py-1 text-[10px]"
          style={{ borderColor: "rgba(192,138,114,.4)", color: C.copperLight }}
        >
          {llmBusy ? "Rémi…" : "Enrichir avec Rémi (LLM)"}
        </button>
      </div>
      <div className="mb-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Stat label="Enveloppes période" value={formatCurrency(data.budgets.period_allocated)} />
        <Stat label="Restant" value={formatCurrency(data.budgets.period_remaining)} />
        <Stat label="Burn estimé / mois" value={formatCurrency(burn)} />
        <Stat
          label="Runway enveloppes"
          value={runway == null ? "—" : `${runway} mois`}
        />
      </div>
      <p className="text-[10px]" style={{ color: C.faint }}>
        {data.assumptions_for_llm} Fiscal ouvert : {formatCurrency(data.fiscal.summary.open_total)}
        {data.fiscal.summary.next_due ? ` · prochaine ${data.fiscal.summary.next_due}` : ""}.
      </p>
      {llmNotes ? (
        <p className="mt-2 text-[11px]" style={{ color: C.warm }}>
          {llmNotes}
        </p>
      ) : null}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border px-2 py-1.5" style={{ borderColor: C.lineSoft }}>
      <p className="text-[9px] uppercase tracking-wide" style={{ color: C.faint }}>
        {label}
      </p>
      <p className="text-[12px] font-medium" style={{ color: C.ivory }}>
        {value}
      </p>
    </div>
  );
}
