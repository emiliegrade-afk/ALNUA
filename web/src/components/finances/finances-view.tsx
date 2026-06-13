"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Plus, Wallet } from "lucide-react";
import { FinancesAccountingPanel } from "@/components/finances/finances-accounting-panel";
import { FinancesControllerPanel } from "@/components/finances/finances-controller-panel";
import { FinancesCharts } from "@/components/finances/finances-charts";
import { FinancesKpiCards } from "@/components/finances/finances-kpi-cards";
import { FinancesMonthNav } from "@/components/finances/finances-month-nav";
import { FinancesRecurringSection } from "@/components/finances/finances-recurring-section";
import { FinancesSummaryCard } from "@/components/finances/finances-summary-card";
import { FinancesTransactionList } from "@/components/finances/finances-transaction-list";
import { FinancesTransactionModal } from "@/components/finances/finances-transaction-modal";
import { Button } from "@/components/ui/button";
import { fetchProjects } from "@/lib/api";
import {
  currentMonthKey,
  fetchFinanceDashboard,
  fetchFinanceSummary,
  fetchFinanceTransactions,
  type FinanceTransaction,
  type FinancialSummary,
  type TransactionType,
} from "@/lib/finances-api";
import type { Project } from "@/lib/types";

export function FinancesView() {
  const [month, setMonth] = useState(currentMonthKey);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);

  const [dashboard, setDashboard] = useState<Awaited<
    ReturnType<typeof fetchFinanceDashboard>
  > | null>(null);
  const [transactions, setTransactions] = useState<FinanceTransaction[]>([]);
  const [summary, setSummary] = useState<FinancialSummary | null>(null);

  const [typeFilter, setTypeFilter] = useState<"all" | TransactionType>("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingTx, setEditingTx] = useState<FinanceTransaction | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [dash, txs] = await Promise.all([
        fetchFinanceDashboard(month),
        fetchFinanceTransactions({ month }),
      ]);
      setDashboard(dash);
      setTransactions(txs);
    } catch {
      setDashboard(null);
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  }, [month]);

  const loadSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      const s = await fetchFinanceSummary(month);
      setSummary(s);
    } catch {
      setSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }, [month]);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      if (typeFilter !== "all" && tx.type !== typeFilter) return false;
      if (categoryFilter !== "all" && tx.category !== categoryFilter) return false;
      return true;
    });
  }, [transactions, typeFilter, categoryFilter]);

  const expenseByCategory = useMemo(() => {
    const out: Record<string, number> = {};
    for (const tx of transactions) {
      if (tx.type !== "expense") continue;
      out[tx.category] = (out[tx.category] ?? 0) + tx.amount;
    }
    return out;
  }, [transactions]);

  function handleRefresh() {
    loadDashboard();
    loadSummary();
  }

  function openCreateModal() {
    setEditingTx(null);
    setModalOpen(true);
  }

  function openEditModal(tx: FinanceTransaction) {
    setEditingTx(tx);
    setModalOpen(true);
  }

  const currentTotals = dashboard?.current_month ?? {
    month,
    total_income: 0,
    total_expenses: 0,
    balance: 0,
  };

  return (
    <div className="space-y-6 pb-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-ivory">
            <Wallet className="h-6 w-6 text-copper" />
            Finances
          </h1>
          <p className="mt-1 text-sm text-titanium">
            Suivi des entrées et sorties — ALNUA solo
          </p>
        </div>
        <FinancesMonthNav month={month} onChange={setMonth} />
      </header>

      {loading && !dashboard ? (
        <div className="flex items-center justify-center py-16 text-titanium">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Chargement…
        </div>
      ) : (
        <>
          <FinancesKpiCards
            totals={currentTotals}
            recurringCount={dashboard?.recurring_expenses.length ?? 0}
            ytdBalance={dashboard?.ytd_balance ?? 0}
          />

          <FinancesSummaryCard
            month={month}
            summary={summary}
            loading={summaryLoading}
            onUpdated={setSummary}
          />

          <FinancesCharts
            months={dashboard?.last_6_months ?? []}
            expenseByCategory={expenseByCategory}
          />

          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-medium text-ivory">Transactions</h2>
              <Button type="button" size="sm" onClick={openCreateModal}>
                <Plus className="mr-2 h-4 w-4" />
                Ajouter une transaction
              </Button>
            </div>

            <FinancesTransactionList
              transactions={filteredTransactions}
              typeFilter={typeFilter}
              categoryFilter={categoryFilter}
              onTypeFilterChange={setTypeFilter}
              onCategoryFilterChange={setCategoryFilter}
              onEdit={openEditModal}
              onDeleted={handleRefresh}
            />
          </section>

          <FinancesRecurringSection
            items={dashboard?.recurring_expenses ?? []}
            onManage={openEditModal}
          />

          <FinancesAccountingPanel
            month={month}
            dashboardData={{
              total_income: currentTotals.total_income,
              total_expenses: currentTotals.total_expenses,
              balance: currentTotals.balance,
              by_category: currentTotals.by_category,
            }}
          />

          <FinancesControllerPanel
            month={month}
            dashboardData={{
              total_income: currentTotals.total_income,
              total_expenses: currentTotals.total_expenses,
              balance: currentTotals.balance,
              by_category: currentTotals.by_category,
            }}
          />
        </>
      )}

      <FinancesTransactionModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        projects={projects}
        transaction={editingTx}
        defaultMonth={month}
        onSaved={handleRefresh}
      />
    </div>
  );
}
