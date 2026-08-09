"use client";

import { useEffect, useState } from "react";
import { FinancesMonthNav } from "@/components/finances/finances-month-nav";
import { FinancesSummaryCard } from "@/components/finances/finances-summary-card";
import { FinancesEvolutionChart, FinancesExpenseDonut } from "@/components/finances/finances-charts";
import { FinancesUpcomingPanel } from "@/components/finances/finances-upcoming-panel";
import { FinancesRecurringPreviewPanel } from "@/components/finances/finances-recurring-preview-panel";
import { FinancesBranchBreakdownPanel } from "@/components/finances/finances-branch-breakdown-panel";
import { formatMonthLabel } from "@/components/finances/finances.constants";
import { fetchAnalyticsSummary } from "@/lib/analytics";
import {
  fetchFinanceSummary,
  formatCurrency,
  type FinanceDashboard,
  type FinancialSummary,
} from "@/lib/finances-api";
import type { Project } from "@/lib/types";
import { C, KpiTile } from "../app-v2/shared";

/* Onglet "Vue globale" — Finance Cockpit. Redesign (suite Phase 29,
   ROADMAP.md) pour se rapprocher de la maquette d'Emilie : 6 tuiles KPI avec
   sparklines réelles (last_6_months), Évolution financière/Répartition des
   dépenses upgradées, 3 nouveaux panneaux (Échéances/Coûts récurrents/
   Branche produit). Règle absolue inchangée : aucune métrique fabriquée —
   MRR affiche "Non renseigné" plutôt qu'un flatTrend(0) trompeur si aucune
   donnée réelle n'existe côté /analytics. Prévisions de trésorerie et
   Investissements restent hors de cette page (génération LLM à la demande /
   aucune source réelle — voir DECISIONS.md et le panneau Contrôleur). */

/** Ligne plate honnête pour une tuile sans historique réel — précédent
 * établi dans web/src/lib/console/rich-data.ts (jamais de série inventée). */
function flatTrend(v: number): number[] {
  return Array.from({ length: 6 }, () => Math.max(0, v));
}

export function VueGlobaleTab({
  month,
  dashboard,
  dashboardLoading,
  onMonthChange,
  projects,
}: {
  month: string;
  dashboard: FinanceDashboard | null;
  dashboardLoading: boolean;
  onMonthChange: (month: string) => void;
  projects: Project[];
}) {
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [mrr, setMrr] = useState<{ value: number | null; change_pct: number | null } | null>(null);

  useEffect(() => {
    let cancelled = false;
    setSummaryLoading(true);
    fetchFinanceSummary(month)
      .then((s) => {
        if (!cancelled) setSummary(s);
      })
      .catch(() => {
        if (!cancelled) setSummary(null);
      })
      .finally(() => {
        if (!cancelled) setSummaryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [month]);

  useEffect(() => {
    let cancelled = false;
    fetchAnalyticsSummary()
      .then((s) => {
        if (!cancelled) setMrr(s.mrr);
      })
      .catch(() => {
        if (!cancelled) setMrr(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const current = dashboard?.current_month;
  const last6 = dashboard?.last_6_months ?? [];
  const last3 = dashboard?.last_3_months ?? [];

  const revenueTrend = last6.map((m) => m.total_income);
  const expenseTrend = last6.map((m) => m.total_expenses);
  const balanceTrend = last6.map((m) => m.balance);
  const cumulativeTrend = balanceTrend.reduce<number[]>((acc, b) => {
    acc.push((acc.length > 0 ? acc[acc.length - 1] : 0) + b);
    return acc;
  }, []);
  const burnRate = last3.length > 0 ? last3.reduce((sum, m) => sum + m.total_expenses, 0) / last3.length : null;

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-1">
      <FinancesMonthNav month={month} onChange={onMonthChange} />

      {dashboardLoading && !dashboard ? (
        <p className="text-center text-[11px]" style={{ color: C.faint }}>
          Chargement du tableau de bord…
        </p>
      ) : (
        <div className="flex flex-wrap gap-3">
          <KpiTile
            label="Revenus (mois)"
            value={current ? formatCurrency(current.total_income) : "—"}
            tone="positive"
            trend={revenueTrend.length > 1 ? revenueTrend : undefined}
            trendColor="#7FC98C"
          />
          <KpiTile
            label="Dépenses (mois)"
            value={current ? formatCurrency(current.total_expenses) : "—"}
            tone="negative"
            trend={expenseTrend.length > 1 ? expenseTrend : undefined}
            trendColor="#f87171"
          />
          <KpiTile
            label="Résultat net (mois)"
            value={current ? formatCurrency(current.balance) : "—"}
            tone={current ? (current.balance >= 0 ? "positive" : "negative") : "default"}
            trend={balanceTrend.length > 1 ? balanceTrend : undefined}
          />
          <KpiTile
            label="Burn rate moyen"
            sublabel="3 derniers mois"
            value={burnRate != null ? formatCurrency(burnRate) : "—"}
            tone="negative"
            trend={expenseTrend.length > 1 ? expenseTrend : undefined}
            trendColor="#f87171"
          />
          <KpiTile
            label="Solde cumulé"
            sublabel="YTD"
            value={dashboard ? formatCurrency(dashboard.ytd_balance) : "—"}
            tone={dashboard ? (dashboard.ytd_balance >= 0 ? "positive" : "negative") : "default"}
            trend={cumulativeTrend.length > 1 ? cumulativeTrend : undefined}
          />
          <KpiTile
            label="MRR"
            value={mrr?.value != null ? formatCurrency(mrr.value) : "Non renseigné"}
            sublabel={mrr?.value != null && mrr.change_pct != null ? `${mrr.change_pct >= 0 ? "+" : ""}${mrr.change_pct.toFixed(1)}% vs mois dernier` : undefined}
            trend={mrr?.value != null ? flatTrend(mrr.value) : undefined}
          />
        </div>
      )}

      <FinancesSummaryCard month={month} summary={summary} loading={summaryLoading} onUpdated={setSummary} />

      <FinancesEvolutionChart months={last6} />
      <FinancesExpenseDonut expenseByCategory={current?.by_category ?? {}} monthLabel={formatMonthLabel(month)} />

      <div className="grid gap-3 lg:grid-cols-3">
        <FinancesUpcomingPanel recurringExpenses={dashboard?.recurring_expenses ?? []} />
        <FinancesRecurringPreviewPanel recurringExpenses={dashboard?.recurring_expenses ?? []} />
        <FinancesBranchBreakdownPanel month={month} projects={projects} />
      </div>
    </div>
  );
}
