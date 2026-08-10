"use client";

import { useEffect, useState } from "react";
import { Loader2, RefreshCw, Shield } from "lucide-react";
import { C } from "@/app/app-v2/shared";
import {
  fetchAgentTrustList,
  fetchTrustGraphRecent,
  trustBand,
  trustBandLabel,
  trustPercent,
  type AgentTrustRow,
  type TrustBand,
  type TrustGraphDecision,
} from "@/lib/trust-api";

const BAND_STYLE: Record<TrustBand, { bar: string; text: string }> = {
  low: { bar: "#c45c4a", text: "#e8a090" },
  review: { bar: C.copperLight, text: C.copperLight },
  autonomous: { bar: "#6a9e7a", text: "#9bc4a8" },
};

function TrustRow({ row }: { row: AgentTrustRow }) {
  const pct = trustPercent(row.score);
  const band = trustBand(row.score);
  const style = BAND_STYLE[band];
  const samples = row.samples ?? 0;

  return (
    <li
      className="rounded-[10px] border px-3 py-2.5"
      style={{ borderColor: C.line, background: "rgba(0,0,0,0.2)" }}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[13px] font-medium" style={{ color: C.ivory }}>
          {row.agent_id}
          {row.provisional ? (
            <span className="ml-2 text-[10px] font-normal" style={{ color: C.dim }}>
              provisoire
            </span>
          ) : null}
        </span>
        <span className="text-[13px] tabular-nums" style={{ color: style.text }}>
          {pct}%
        </span>
      </div>
      <div
        className="mt-2 h-1.5 overflow-hidden rounded-full"
        style={{ background: "rgba(255,255,255,0.06)" }}
      >
        <div
          className="h-full rounded-full transition-[width]"
          style={{ width: `${pct}%`, background: style.bar }}
        />
      </div>
      <div className="mt-1.5 flex justify-between text-[10px]" style={{ color: C.dim }}>
        <span>{trustBandLabel(band)}</span>
        <span>
          {samples} échantillon{samples === 1 ? "" : "s"}
          {row.successes != null || row.failures != null
            ? ` · ${row.successes ?? 0}✓ / ${row.failures ?? 0}✗`
            : ""}
        </span>
      </div>
    </li>
  );
}

function DecisionRow({ d }: { d: TrustGraphDecision }) {
  const ok = d.allowed;
  return (
    <li
      className="flex flex-wrap items-baseline justify-between gap-2 rounded-[8px] border px-2.5 py-2 text-[11px]"
      style={{ borderColor: C.line, background: "rgba(0,0,0,0.15)" }}
    >
      <span style={{ color: C.ivory }}>
        <span className="font-medium">{d.agent_id}</span>
        <span style={{ color: C.dim }}> · {d.capability}</span>
      </span>
      <span style={{ color: ok ? "#9bc4a8" : "#e8a090" }}>
        {ok ? "allow" : "deny"}
        {d.reason ? ` · ${d.reason}` : ""}
      </span>
    </li>
  );
}

/** Phase 31 scores + Phase E Trust Graph decisions (DEC-011 / DEC-026). */
export function AgentTrustView() {
  const [rows, setRows] = useState<AgentTrustRow[]>([]);
  const [decisions, setDecisions] = useState<TrustGraphDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [trustRows, graph] = await Promise.all([
        fetchAgentTrustList(80),
        fetchTrustGraphRecent(25),
      ]);
      setRows(trustRows);
      setDecisions(graph);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chargement trust impossible");
      setRows([]);
      setDecisions([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2">
          <Shield className="mt-0.5 h-4 w-4 shrink-0" style={{ color: C.copperLight }} />
          <div>
            <p className="text-[12px] leading-snug" style={{ color: C.dim }}>
              Indice de confiance distinct de la compétition (DEC-011).{" "}
              {"<70 % → validation manager · 70–90 % → Review Board · >90 % → autonomie."}
              {" "}PermissionGuard (DEC-026) journalise allow/deny ci-dessous.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] disabled:opacity-50"
          style={{ borderColor: C.line, color: C.titanium }}
        >
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
          Rafraîchir
        </button>
      </div>

      {error ? (
        <p className="rounded-[10px] border px-3 py-2 text-[12px]" style={{ borderColor: "#c45c4a55", color: "#e8a090" }}>
          {error}
        </p>
      ) : null}

      {loading && rows.length === 0 ? (
        <div className="flex items-center gap-2 py-8 text-[12px]" style={{ color: C.dim }}>
          <Loader2 className="h-4 w-4 animate-spin" />
          Chargement des scores…
        </div>
      ) : null}

      {!loading && !error && rows.length === 0 ? (
        <p className="rounded-[10px] border px-3 py-4 text-[12px]" style={{ borderColor: C.line, color: C.dim }}>
          Aucun score enregistré — les agents restent au défaut 70 % (provisoire) jusqu’à
          la première validation workflow / Review Board.
        </p>
      ) : null}

      {rows.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {rows.map((row) => (
            <TrustRow key={row.agent_id} row={row} />
          ))}
        </ul>
      ) : null}

      <div className="mt-2">
        <h2 className="mb-2 text-[12px] font-medium tracking-wide" style={{ color: C.titanium }}>
          DÉCISIONS RÉCENTES (Trust Graph)
        </h2>
        {decisions.length === 0 && !loading ? (
          <p className="text-[11px]" style={{ color: C.dim }}>
            Aucune décision PermissionGuard pour l’instant.
          </p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {decisions.map((d, i) => (
              <DecisionRow key={`${d.ts ?? i}-${d.agent_id}-${d.capability}`} d={d} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
