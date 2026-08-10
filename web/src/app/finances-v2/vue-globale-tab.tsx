"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FinancesMonthNav } from "@/components/finances/finances-month-nav";
import { FinancesSummaryCard } from "@/components/finances/finances-summary-card";
import {
  FinancesEvolutionChart,
  FinancesExpenseDonut,
} from "@/components/finances/finances-charts";
import { FinancesUpcomingPanel } from "@/components/finances/finances-upcoming-panel";
import { FinancesRecurringPreviewPanel } from "@/components/finances/finances-recurring-preview-panel";
import { FinancesBranchBreakdownPanel } from "@/components/finances/finances-branch-breakdown-panel";
import {
  FinanceKpiCard,
  FinanceTransactionRow,
  formatPct,
  formatTxDate,
  pctChange,
} from "@/components/finances/finance-kpi-card";
import { formatMonthLabel } from "@/components/finances/finances.constants";
import { fetchAnalyticsSummary } from "@/lib/analytics";
import {
  fetchFinanceInvoices,
  fetchFinanceSummary,
  fetchFinanceTransactions,
  formatCurrency,
  type FinanceDashboard,
  type FinanceTransaction,
  type FinancialSummary,
} from "@/lib/finances-api";
import type { Project } from "@/lib/types";
import { ROUTES } from "@/lib/routes";

/* Vue globale Finance — brand board grid. Pas de métrique inventée. */

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
  const [mrr, setMrr] = useState<{
    value: number | null;
    change_pct: number | null;
  } | null>(null);
  const [toPay, setToPay] = useState<{ count: number; total: number } | null>(
    null,
  );
  const [recentTx, setRecentTx] = useState<FinanceTransaction[]>([]);

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
    fetchFinanceInvoices()
      .then((inv) => {
        if (!cancelled) {
          setToPay({
            count: inv.summary.to_pay_count,
            total: inv.summary.to_pay_total,
          });
        }
      })
      .catch(() => {
        if (!cancelled) setToPay(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchFinanceTransactions({ month })
      .then((txs) => {
        if (!cancelled) {
          setRecentTx(
            [...txs]
              .sort((a, b) => b.date.localeCompare(a.date))
              .slice(0, 6),
          );
        }
      })
      .catch(() => {
        if (!cancelled) setRecentTx([]);
      });
    return () => {
      cancelled = true;
    };
  }, [month]);

  const current = dashboard?.current_month;
  const last6 = dashboard?.last_6_months ?? [];
  const last3 = dashboard?.last_3_months ?? [];
  const prev = last6.length >= 2 ? last6[last6.length - 2] : null;

  const expenseTrend = last6.map((m) => m.total_expenses);
  const balanceTrend = last6.map((m) => m.balance);
  const cumulativeTrend = balanceTrend.reduce<number[]>((acc, b) => {
    acc.push((acc.length > 0 ? acc[acc.length - 1] : 0) + b);
    return acc;
  }, []);

  const burnRate =
    last3.length > 0
      ? last3.reduce((sum, m) => sum + m.total_expenses, 0) / last3.length
      : null;
  const earlier = last6.length > 3 ? last6.slice(0, -3) : [];
  const prevBurn =
    earlier.length > 0
      ? earlier.reduce((s, m) => s + m.total_expenses, 0) / earlier.length
      : null;

  const ytdPrev = (dashboard?.ytd_balance ?? 0) - (current?.balance ?? 0);
  const cashChange = formatPct(
    dashboard ? pctChange(dashboard.ytd_balance, ytdPrev) : null,
  );
  const profitChange = formatPct(
    current && prev ? pctChange(current.balance, prev.balance) : null,
  );
  const burnChange = formatPct(
    burnRate != null && prevBurn != null ? pctChange(burnRate, prevBurn) : null,
  );
  // Burn down = good → invert positive styling when change is negative
  const burnIsGood = burnChange != null && burnChange.startsWith("-");

  const mrrChange =
    mrr?.value != null && mrr.change_pct != null
      ? formatPct(mrr.change_pct)
      : null;

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto p-1">
      <FinancesMonthNav month={month} onChange={onMonthChange} />

      {dashboardLoading && !dashboard ? (
        <p className="text-center text-sm text-alnua-titane">
          Chargement du tableau de bord…
        </p>
      ) : (
        <div className="grid grid-cols-12 gap-6">
          <FinanceKpiCard
            className="col-span-12 sm:col-span-6 lg:col-span-3"
            title="Cash flow"
            value={dashboard ? formatCurrency(dashboard.ytd_balance) : "—"}
            change={dashboard ? cashChange : null}
            isPositive={(dashboard?.ytd_balance ?? 0) >= 0}
            trend={cumulativeTrend.length > 1 ? cumulativeTrend : undefined}
            trendColor="#2DD4BF"
          />
          <FinanceKpiCard
            className="col-span-12 sm:col-span-6 lg:col-span-3"
            title="MRR"
            value={
              mrr?.value != null ? formatCurrency(mrr.value) : "Non renseigné"
            }
            change={mrrChange}
            isPositive={(mrr?.change_pct ?? 0) >= 0}
            trend={mrr?.value != null ? flatTrend(mrr.value) : undefined}
          />
          <FinanceKpiCard
            className="col-span-12 sm:col-span-6 lg:col-span-3"
            title="Burn rate"
            value={
              burnRate != null ? `${formatCurrency(burnRate)} / mois` : "—"
            }
            change={burnChange}
            isPositive={burnIsGood}
            trend={expenseTrend.length > 1 ? expenseTrend : undefined}
            trendColor="#F87171"
          />
          <FinanceKpiCard
            className="col-span-12 sm:col-span-6 lg:col-span-3"
            title="Profit (mois)"
            value={current ? formatCurrency(current.balance) : "—"}
            change={profitChange}
            isPositive={(current?.balance ?? 0) >= 0}
            trend={balanceTrend.length > 1 ? balanceTrend : undefined}
          />

          <div className="col-span-12 lg:col-span-8">
            <FinancesEvolutionChart months={last6} />
          </div>
          <div className="col-span-12 lg:col-span-4">
            <FinancesExpenseDonut
              expenseByCategory={current?.by_category ?? {}}
              monthLabel={formatMonthLabel(month)}
            />
          </div>

          <div className="col-span-12 rounded-xl border border-alnua-border bg-alnua-surface p-5 lg:col-span-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-alnua-titane">
                Dernières transactions
              </h3>
              {toPay && toPay.count > 0 ? (
                <span className="text-[11px] text-alnua-danger">
                  {toPay.count} facture{toPay.count > 1 ? "s" : ""} ·{" "}
                  {formatCurrency(toPay.total)}
                </span>
              ) : null}
            </div>
            {recentTx.length === 0 ? (
              <p className="text-sm text-alnua-titane">
                Aucune transaction ce mois.
              </p>
            ) : (
              <table className="w-full text-sm">
                <tbody className="divide-y divide-alnua-border/50">
                  {recentTx.map((tx) => (
                    <FinanceTransactionRow
                      key={tx.id}
                      date={formatTxDate(tx.date)}
                      label={
                        tx.description?.trim() ||
                        tx.project_name ||
                        tx.category
                      }
                      amount={`${tx.type === "income" ? "+" : "-"}${formatCurrency(tx.amount)}`}
                      type={tx.type === "income" ? "in" : "out"}
                    />
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="col-span-12 grid gap-3 lg:col-span-6 lg:grid-cols-1">
            <FinancesUpcomingPanel
              recurringExpenses={dashboard?.recurring_expenses ?? []}
            />
          </div>
        </div>
      )}

      {toPay && toPay.count > 0 ? (
        <p className="text-[11px] text-alnua-titane/60">
          Paiement externe uniquement — détail dans Coûts &amp; Factures
          {" · "}
          <Link
            href={ROUTES.finances}
            className="underline underline-offset-2 text-alnua-titane"
          >
            ouvrir Comptabilité
          </Link>
        </p>
      ) : null}

      <FinancesSummaryCard
        month={month}
        summary={summary}
        loading={summaryLoading}
        onUpdated={setSummary}
      />

      <div className="grid gap-3 lg:grid-cols-2">
        <FinancesRecurringPreviewPanel
          recurringExpenses={dashboard?.recurring_expenses ?? []}
        />
        <FinancesBranchBreakdownPanel month={month} projects={projects} />
      </div>
    </div>
  );
}
