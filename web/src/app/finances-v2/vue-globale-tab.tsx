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
  fetchBudgetAlerts,
  fetchFinanceInvoices,
  fetchFinanceSummary,
  fetchFinanceTransactions,
  fetchFiscalObligations,
  formatCurrency,
  type BudgetAlertsResponse,
  type FinanceDashboard,
  type FinanceTransaction,
  type FinancialSummary,
  type FiscalSummary,
} from "@/lib/finances-api";
import type { Project } from "@/lib/types";
import { ROUTES } from "@/lib/routes";

/* Vue globale — disposition maquette PÔLE COMPTABILITÉ :
   6 KPI → Evolution+Donut+Échéances+SaaS → Branch+Résumé+Tx+Récurrents.
   Métriques réelles uniquement (runway = cash / burn). */

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
  const [budgetAlerts, setBudgetAlerts] = useState<BudgetAlertsResponse | null>(
    null,
  );
  const [fiscalSummary, setFiscalSummary] = useState<FiscalSummary | null>(null);
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
    fetchBudgetAlerts(month)
      .then((a) => {
        if (!cancelled) setBudgetAlerts(a);
      })
      .catch(() => {
        if (!cancelled) setBudgetAlerts(null);
      });
    fetchFiscalObligations()
      .then((f) => {
        if (!cancelled) setFiscalSummary(f.summary);
      })
      .catch(() => {
        if (!cancelled) setFiscalSummary(null);
      });
    return () => {
      cancelled = true;
    };
  }, [month]);

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
  const incomeTrend = last6.map((m) => m.total_income);
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

  const cashPosition = dashboard?.ytd_balance ?? 0;
  const runwayMonths =
    burnRate != null && burnRate > 0 && cashPosition > 0
      ? cashPosition / burnRate
      : null;

  const profitChange = formatPct(
    current && prev ? pctChange(current.balance, prev.balance) : null,
  );
  const burnChange = formatPct(
    burnRate != null && prevBurn != null ? pctChange(burnRate, prevBurn) : null,
  );
  const burnIsGood = burnChange != null && burnChange.startsWith("-");
  const soldeChange = formatPct(
    dashboard && current
      ? pctChange(cashPosition, cashPosition - current.balance)
      : null,
  );

  const mrrChange =
    mrr?.value != null && mrr.change_pct != null
      ? formatPct(mrr.change_pct)
      : null;

  return (
    <div className="alnua-scroll dept-hud flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto py-1">
      <div className="flex items-center justify-between gap-3 px-0.5">
        <FinancesMonthNav month={month} onChange={onMonthChange} />
      </div>

      {dashboardLoading && !dashboard ? (
        <p className="text-center text-sm text-titanium/50">
          Chargement du tableau de bord…
        </p>
      ) : (
        <div className="flex flex-col gap-5">
          {/* Rangée 1 — rail KPI unique (pas 6 cartes) */}
          <div className="finance-kpi-rail grid-cols-2 sm:grid-cols-3 xl:grid-cols-6">
            <FinanceKpiCard
              title="Cash Flow"
              value={current ? formatCurrency(current.total_income) : "—"}
              change={
                current && prev
                  ? formatPct(pctChange(current.total_income, prev.total_income))
                  : null
              }
              isPositive={
                current && prev
                  ? current.total_income >= prev.total_income
                  : (current?.total_income ?? 0) >= 0
              }
              trend={incomeTrend.length > 1 ? incomeTrend : undefined}
              trendColor="#3DDC97"
            />
            <FinanceKpiCard
              title="MRR"
              value={
                mrr?.value != null ? formatCurrency(mrr.value) : "Non renseigné"
              }
              change={mrrChange}
              isPositive={(mrr?.change_pct ?? 0) >= 0}
              trend={mrr?.value != null ? flatTrend(mrr.value) : undefined}
              trendColor="#E09B6A"
            />
            <FinanceKpiCard
              title="Burn Rate"
              value={
                burnRate != null ? `${formatCurrency(burnRate)} /mois` : "—"
              }
              change={burnChange}
              isPositive={burnIsGood}
              trend={expenseTrend.length > 1 ? expenseTrend : undefined}
              trendColor="#F87171"
            />
            <FinanceKpiCard
              title="Runway"
              value={
                runwayMonths != null ? `${runwayMonths.toFixed(1)} mois` : "—"
              }
              change={null}
              isPositive={(runwayMonths ?? 0) >= 6}
              trend={cumulativeTrend.length > 1 ? cumulativeTrend : undefined}
              trendColor="#7BA7D9"
            />
            <FinanceKpiCard
              title="Profit"
              value={current ? formatCurrency(current.balance) : "—"}
              change={profitChange}
              isPositive={(current?.balance ?? 0) >= 0}
              trend={balanceTrend.length > 1 ? balanceTrend : undefined}
              trendColor="#F5C9A4"
            />
            <FinanceKpiCard
              title="Solde"
              value={dashboard ? formatCurrency(cashPosition) : "—"}
              change={soldeChange}
              isPositive={cashPosition >= 0}
              trend={cumulativeTrend.length > 1 ? cumulativeTrend : undefined}
              trendColor="#2DD4BF"
            />
          </div>

          {/* Rangée 2 — chart hero + 3 instruments latéraux */}
          <div className="grid grid-cols-12 gap-3">
            <div className="col-span-12 xl:col-span-6">
              <FinancesEvolutionChart months={last6} />
            </div>
            <div className="col-span-12 sm:col-span-4 xl:col-span-2">
              <FinancesExpenseDonut
                expenseByCategory={current?.by_category ?? {}}
                monthLabel={formatMonthLabel(month)}
              />
            </div>
            <div className="col-span-12 sm:col-span-4 xl:col-span-2">
              <FinancesUpcomingPanel
                recurringExpenses={dashboard?.recurring_expenses ?? []}
              />
            </div>
            <div className="col-span-12 sm:col-span-4 xl:col-span-2">
              <FinancesRecurringPreviewPanel
                recurringExpenses={dashboard?.recurring_expenses ?? []}
              />
            </div>
          </div>

          {/* Rangée 3 */}
          <div className="grid grid-cols-12 gap-3">
            <div className="col-span-12 lg:col-span-3">
              <FinancesBranchBreakdownPanel month={month} projects={projects} />
            </div>
            <div className="col-span-12 lg:col-span-3">
              <FinancesSummaryCard
                month={month}
                summary={summary}
                loading={summaryLoading}
                onUpdated={setSummary}
              />
            </div>
            <div className="finance-instrument col-span-12 p-4 lg:col-span-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <h3 className="text-[9px] font-medium uppercase tracking-[0.24em] text-titanium">
                  Transactions
                </h3>
                {toPay && toPay.count > 0 ? (
                  <span className="text-[10px] text-danger">
                    {toPay.count} · {formatCurrency(toPay.total)}
                  </span>
                ) : null}
              </div>
              {recentTx.length === 0 ? (
                <p className="text-xs text-titanium/50">Aucune ce mois.</p>
              ) : (
                <table className="w-full">
                  <tbody className="divide-y divide-titanium/10">
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
            <div className="finance-instrument col-span-12 flex flex-col p-4 lg:col-span-3">
              <h3 className="text-[9px] font-medium uppercase tracking-[0.24em] text-titanium">
                À payer
              </h3>
              <p className="mt-4 font-display text-[1.75rem] font-light tracking-tight text-ivoire">
                {toPay ? formatCurrency(toPay.total) : "—"}
              </p>
              <p className="mt-1 text-[11px] text-titanium/70">
                {toPay && toPay.count > 0
                  ? `${toPay.count} facture${toPay.count > 1 ? "s" : ""}`
                  : "Aucune facture ouverte"}
              </p>
              {budgetAlerts && budgetAlerts.warning_count + budgetAlerts.critical_count > 0 ? (
                <p className="mt-2 text-[10px] text-copper-light/90">
                  Budgets : {budgetAlerts.critical_count} critique
                  {budgetAlerts.critical_count !== 1 ? "s" : ""}
                  {budgetAlerts.warning_count > 0
                    ? ` · ${budgetAlerts.warning_count} alerte${budgetAlerts.warning_count > 1 ? "s" : ""}`
                    : ""}
                </p>
              ) : null}
              {fiscalSummary?.next_due ? (
                <p className="mt-1 text-[10px] text-titanium/55">
                  Fiscal : {fiscalSummary.next_due_title ?? "échéance"}{" "}
                  {fiscalSummary.next_due.slice(0, 10)}
                </p>
              ) : null}
              <p className="mt-auto pt-6 text-[10px] text-titanium/45">
                Paiement externe ·{" "}
                <Link
                  href={ROUTES.finances}
                  className="text-copper-light/80 underline-offset-2 hover:underline"
                >
                  Coûts &amp; Factures
                </Link>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
