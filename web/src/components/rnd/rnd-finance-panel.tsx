"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RndFinanceJson } from "@/lib/rnd-dossier";

interface RndFinancePanelProps {
  finance: RndFinanceJson | null | undefined;
  stale?: boolean;
}

function normalizeFinance(finance: RndFinanceJson): RndFinanceJson & { _stale?: boolean } {
  const rev = { ...(finance.revenue_hypothesis ?? {}) };
  if (rev.m12_monthly_run_rate_eur == null && rev.revenue_m12_eur != null) {
    rev.m12_monthly_run_rate_eur = rev.revenue_m12_eur;
  }
  if (rev.m6_monthly_run_rate_eur == null && rev.revenue_m6_eur != null) {
    rev.m6_monthly_run_rate_eur = rev.revenue_m6_eur;
  }
  if (rev.cumulative_12m_eur == null && rev.m12_monthly_run_rate_eur != null) {
    const m12 = rev.m12_monthly_run_rate_eur;
    const m6 = rev.m6_monthly_run_rate_eur ?? m12 * 0.4;
    rev.cumulative_6m_eur = Math.round(m6 * 3);
    rev.cumulative_12m_eur = Math.round(m6 * 3 + (m6 + m12) * 3);
  }

  const stale =
    finance.finance_version == null &&
    finance.cost_model !== "ai_solo" &&
    (finance.capex_dev_eur ?? 0) > 400 &&
    (finance.capex_llm_agents_eur ?? 0) === 0;

  return { ...finance, revenue_hypothesis: rev, _stale: stale };
}

export function RndFinancePanel({ finance, stale: staleProp }: RndFinancePanelProps) {
  const normalized = useMemo(
    () => (finance ? normalizeFinance(finance) : null),
    [finance]
  );

  if (!normalized) {
    return (
      <div className="rounded-xl border border-copper/10 bg-white/[0.02] p-4 text-sm text-titanium/50">
        Business case non généré — ouvre le dossier pour recalculer.
      </div>
    );
  }

  const stale = staleProp ?? normalized._stale;
  const isAi = normalized.cost_model === "ai_solo" && !stale;
  const rev = normalized.revenue_hypothesis ?? {};

  const agentCapex = isAi
    ? (normalized.capex_llm_agents_eur ?? 0)
    : stale
      ? 0
      : (normalized.capex_dev_eur ?? 0);

  const costChart = isAi
    ? [
        { name: "Agents IA", value: normalized.capex_llm_agents_eur ?? 0 },
        { name: "Dossier LLM", value: normalized.capex_dossier_llm_eur ?? 0 },
        { name: "Marketing", value: normalized.capex_marketing_eur ?? 0 },
      ].filter((x) => x.value > 0)
    : stale
      ? [{ name: "⚠ ancien modèle", value: normalized.capex_eur ?? 0 }]
      : [
          { name: "Dev humain", value: normalized.capex_dev_eur ?? 0 },
          { name: "Marketing", value: normalized.capex_marketing_eur ?? 0 },
        ];

  const m3 = rev.m3_monthly_run_rate_eur ?? 0;
  const m6 = rev.m6_monthly_run_rate_eur ?? 0;
  const m12 = rev.m12_monthly_run_rate_eur ?? 0;
  const hasRevenue = m3 > 0 || m6 > 0 || m12 > 0;
  const pricing = rev.pricing_model;
  const subs = rev.paying_subscribers;
  const arpu = rev.blended_arpu_eur ?? pricing?.blended_arpu_eur ?? 0;

  const revenueChart = hasRevenue
    ? [
        { month: "M1", median: m3 * 0.4 },
        { month: "M2", median: m3 * 0.72 },
        { month: "M3", median: m3 },
        { month: "M6", median: m6 },
        { month: "M9", median: (m6 + m12) / 2 },
        { month: "M12", median: m12 },
      ]
    : [];

  const capex = normalized.capex_eur ?? 0;
  const opexIncr = normalized.opex_incremental_eur ?? normalized.opex_monthly_eur ?? 0;
  const invest12m = capex + opexIncr * 12;
  const return12m = rev.cumulative_12m_eur ?? normalized.net_impact_12m_eur ?? 0;
  const roiPct = invest12m > 0 ? Math.round(((return12m - invest12m) / invest12m) * 100) : null;

  const verdictCls =
    normalized.verdict_finance === "viable"
      ? "text-emerald-400 border-emerald-500/25 bg-emerald-500/10"
      : normalized.verdict_finance === "no_go"
        ? "text-red-400 border-red-500/25 bg-red-500/10"
        : "text-amber-400 border-amber-500/25 bg-amber-500/10";

  return (
    <div className="space-y-5 rounded-xl border border-copper/15 bg-copper/[0.03] p-4 sm:p-5">
      {stale ? (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
          Estimation obsolète (modèle « dev humain 50 €/h »). Recharge le dossier — recalcul
          automatique au prochain chargement avec le modèle <strong>solo + agents IA</strong>.
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-ivory/90">Business case</h3>
          <p className="text-[10px] text-titanium/50">
            {isAi ? "Solo + agents IA (OpenRouter)" : stale ? "Données à recalculer" : "Modèle legacy"}
          </p>
        </div>
        <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${verdictCls}`}>
          {normalized.verdict_finance?.toUpperCase() ?? "?"}
        </span>
      </div>

      {!stale && (normalized.portfolio_apps_count ?? 0) > 0 ? (
        <div className="rounded-lg border border-emerald-500/15 bg-emerald-500/5 px-3 py-2 text-xs text-emerald-200/90">
          Portfolio ALNUA : <strong>{normalized.portfolio_apps_count} apps</strong> ·{" "}
          <strong>~{normalized.portfolio_monthly_revenue_eur?.toFixed(0) ?? 0} €/mois</strong> actuels
        </div>
      ) : null}

      {!stale && pricing?.tiers?.length ? (
        <div className="rounded-lg border border-copper/20 bg-obsidian/40 p-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-copper/80">
            Grille tarifaire produit
          </p>
          <div className="mb-2 flex flex-wrap gap-2 text-[10px] text-titanium/55">
            <span>
              Fourchette :{" "}
              <strong className="text-ivory/80">
                {pricing.price_range_eur?.min?.toFixed(0)} – {pricing.price_range_eur?.max?.toFixed(0)} €/mois
              </strong>
            </span>
            <span>
              ARPU médian : <strong className="text-copper">{arpu.toFixed(0)} €/mois</strong>
            </span>
            {subs ? (
              <span>
                Clients payants (M3/M6/M12) :{" "}
                <strong className="text-ivory/80">
                  {subs.m3} / {subs.m6} / {subs.m12}
                </strong>
              </span>
            ) : null}
          </div>
          <div className="grid gap-1.5 sm:grid-cols-2">
            {pricing.tiers.map((tier) => (
              <div
                key={tier.name}
                className="flex items-center justify-between rounded-md border border-white/6 bg-white/[0.02] px-2 py-1.5 text-xs"
              >
                <span className="text-ivory/85">{tier.name}</span>
                <span className="font-medium text-copper">
                  {tier.price_eur.toFixed(2)} €
                  {tier.mix_pct != null ? (
                    <span className="ml-1 text-[10px] text-titanium/45">
                      ({Math.round(tier.mix_pct * 100)} % mix)
                    </span>
                  ) : null}
                </span>
              </div>
            ))}
          </div>
          {pricing.promo_note ? (
            <p className="mt-2 text-[10px] italic text-titanium/45">{pricing.promo_note}</p>
          ) : null}
        </div>
      ) : null}

      {/* Comment mesurer l'investissement */}
      <div className="rounded-lg border border-copper/20 bg-obsidian/40 p-3">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-copper/80">
          Comment mesurer ton investissement
        </p>
        <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
          <div>
            <p className="text-titanium/50">Tu mets (CAPEX)</p>
            <p className="font-semibold text-copper">
              {stale ? "→ recalcul" : `${capex.toFixed(0)} €`}
            </p>
            <p className="text-[10px] text-titanium/45">one-shot lancement</p>
          </div>
          <div>
            <p className="text-titanium/50">Coût 12 mois total</p>
            <p className="font-semibold text-ivory/90">
              {stale ? "—" : `${invest12m.toFixed(0)} €`}
            </p>
            <p className="text-[10px] text-titanium/45">CAPEX + OPEX incrémental × 12</p>
          </div>
          <div>
            <p className="text-titanium/50">Tu récupères (12 mois)</p>
            <p className="font-semibold text-emerald-400/90">
              {hasRevenue || normalized.net_impact_12m_eur != null
                ? `${(rev.cumulative_12m_eur ?? normalized.net_impact_12m_eur ?? 0).toFixed(0)} €`
                : "—"}
            </p>
            <p className="text-[10px] text-titanium/45">revenus cumulés si ça marche</p>
          </div>
          <div>
            <p className="text-titanium/50">ROI 12 mois</p>
            <p
              className={`font-semibold ${
                roiPct != null && roiPct >= 0 ? "text-emerald-400" : "text-amber-400"
              }`}
            >
              {roiPct != null ? `${roiPct > 0 ? "+" : ""}${roiPct} %` : "—"}
            </p>
            <p className="text-[10px] text-titanium/45">(revenus − investissement) / investissement</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
        <div>
          <p className="text-titanium/50">Agents IA (dev)</p>
          <p className="text-lg font-semibold text-copper">
            {stale ? "obsolète" : `${agentCapex.toFixed(0)} €`}
          </p>
        </div>
        <div>
          <p className="text-titanium/50">OPEX +/mois</p>
          <p className="text-lg font-semibold text-ivory/90">
            {(normalized.opex_incremental_eur ?? normalized.opex_monthly_eur ?? 0).toFixed(0)} €
          </p>
        </div>
        <div>
          <p className="text-titanium/50">Revenu M3 (run-rate)</p>
          <p className="text-lg font-semibold text-emerald-400/90">
            {m3 > 0 ? `${m3.toFixed(0)} €/mois` : "—"}
          </p>
        </div>
        <div>
          <p className="text-titanium/50">Revenu M12 (run-rate)</p>
          <p className="text-lg font-semibold text-emerald-400/90">
            {m12 > 0 ? `${m12.toFixed(0)} €/mois` : "—"}
          </p>
        </div>
        <div>
          <p className="text-titanium/50">Impact net 12 mois</p>
          <p
            className={`text-lg font-semibold ${
              (normalized.net_impact_12m_eur ?? 0) >= 0 ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {normalized.net_impact_12m_eur != null
              ? `${normalized.net_impact_12m_eur.toFixed(0)} €`
              : hasRevenue
                ? `${((rev.cumulative_12m_eur ?? 0) - invest12m).toFixed(0)} €`
                : "—"}
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-titanium/50">
            Coûts de lancement
          </p>
          <div className="h-36 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={costChart} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 9 }} />
                <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} width={36} />
                <Tooltip
                  contentStyle={{
                    background: "#1a1a1f",
                    border: "1px solid rgba(184,115,51,0.3)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(v) => [`${v ?? 0} EUR`, ""]}
                />
                <Bar dataKey="value" fill={stale ? "#f59e0b" : "#b87333"} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-titanium/50">
            Revenus projetés (€/mois si le produit fonctionne)
          </p>
          {hasRevenue ? (
            <div className="h-36 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={revenueChart} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="month" tick={{ fill: "#9ca3af", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} width={36} />
                  <Tooltip
                    contentStyle={{
                      background: "#1a1a1f",
                      border: "1px solid rgba(46,125,50,0.3)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(v) => [`${v ?? 0} EUR/mois`, "Médian"]}
                  />
                  <Line
                    type="monotone"
                    dataKey="median"
                    stroke="#4ade80"
                    strokeWidth={2}
                    dot={{ fill: "#4ade80", r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="flex h-36 items-center justify-center text-xs text-titanium/50">
              Revenus non calculés — recalcule le business case
            </p>
          )}
        </div>
      </div>

      {hasRevenue ? (
        <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
          <div className="rounded-lg border border-white/8 bg-white/[0.02] p-2">
            <p className="text-titanium/50">Cumul 6 mois</p>
            <p className="text-sm font-medium text-ivory/90">{rev.cumulative_6m_eur?.toFixed(0) ?? "—"} €</p>
          </div>
          <div className="rounded-lg border border-white/8 bg-white/[0.02] p-2">
            <p className="text-titanium/50">Cumul 12 mois</p>
            <p className="text-sm font-medium text-ivory/90">{rev.cumulative_12m_eur?.toFixed(0) ?? "—"} €</p>
          </div>
          <div className="rounded-lg border border-white/8 bg-white/[0.02] p-2">
            <p className="text-titanium/50">Prudent / Optimiste M12</p>
            <p className="text-sm font-medium text-ivory/90">
              {rev.conservative_m12_monthly_eur?.toFixed(0) ?? Math.round(m12 * 0.35)} /{" "}
              {rev.optimistic_m12_monthly_eur?.toFixed(0) ?? Math.round(m12 * 2.2)} €/mois
            </p>
          </div>
        </div>
      ) : null}

      {normalized.reasoning ? (
        <p className="text-xs leading-relaxed text-titanium/70">{normalized.reasoning}</p>
      ) : null}
    </div>
  );
}
