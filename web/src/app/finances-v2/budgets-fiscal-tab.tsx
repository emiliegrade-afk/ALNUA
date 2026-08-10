"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { ForecastCockpitPanel } from "@/components/finances/forecast-cockpit-panel";
import {
  createFinanceBudget,
  createFiscalObligation,
  fetchBudgetAlerts,
  fetchFinanceBudgets,
  fetchFiscalObligations,
  formatCurrency,
  updateFinanceBudget,
  updateFiscalObligation,
  type BudgetDepartmentAlert,
  type BudgetSummary,
  type FinanceBudget,
  type FiscalObligation,
  type FiscalSummary,
} from "@/lib/finances-api";
import { C } from "../app-v2/shared";
import { BudgetsSection, FiscalSection, MiniStat } from "./budgets-fiscal-sections";

export function BudgetsFiscalTab() {
  const [budgets, setBudgets] = useState<FinanceBudget[]>([]);
  const [obligations, setObligations] = useState<FiscalObligation[]>([]);
  const [bSum, setBSum] = useState<BudgetSummary | null>(null);
  const [fSum, setFSum] = useState<FiscalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [dept, setDept] = useState("marketing");
  const [period, setPeriod] = useState(() => new Date().toISOString().slice(0, 7));
  const [amount, setAmount] = useState("");
  const [fiscalTitle, setFiscalTitle] = useState("");
  const [fiscalAmount, setFiscalAmount] = useState("");
  const [fiscalDue, setFiscalDue] = useState(() => new Date().toISOString().slice(0, 10));
  const [fiscalKind, setFiscalKind] = useState("tva");
  const [saving, setSaving] = useState(false);
  const [alertsByDept, setAlertsByDept] = useState<Record<string, BudgetDepartmentAlert>>({});

  async function load() {
    setLoading(true);
    try {
      const [b, f, alerts] = await Promise.all([
        fetchFinanceBudgets(),
        fetchFiscalObligations(),
        fetchBudgetAlerts(period),
      ]);
      setBudgets(b.budgets);
      setBSum(b.summary);
      setObligations(f.obligations);
      setFSum(f.summary);
      setAlertsByDept(Object.fromEntries(alerts.alerts.map((a) => [a.department, a])));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Chargement budgets/fiscal impossible");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [period]);

  async function addBudget() {
    const value = parseFloat(amount);
    if (!dept.trim() || Number.isNaN(value) || value < 0) return;
    setSaving(true);
    try {
      await createFinanceBudget({ department: dept.trim(), period, amount: value });
      toast.success("Enveloppe créée (pas de transfert auto).");
      setAmount("");
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  async function addFiscal() {
    const value = parseFloat(fiscalAmount);
    if (!fiscalTitle.trim() || Number.isNaN(value) || value < 0) return;
    setSaving(true);
    try {
      await createFiscalObligation({
        title: fiscalTitle.trim(),
        amount: value,
        due_date: fiscalDue || undefined,
        kind: fiscalKind,
        status: "upcoming",
      });
      toast.success("Obligation ajoutée (paiement hors Hub).");
      setFiscalTitle("");
      setFiscalAmount("");
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  async function markPaid(id: string) {
    try {
      await updateFiscalObligation(id, { status: "paid_externally" });
      toast.success("Marquée payée en externe.");
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  }

  async function setSpent(id: string, current: number) {
    const raw = window.prompt("Dépensé (€)", String(current ?? 0));
    if (raw == null) return;
    const value = parseFloat(raw);
    if (Number.isNaN(value) || value < 0) {
      toast.error("Montant invalide");
      return;
    }
    try {
      await updateFinanceBudget(id, { spent: value });
      toast.success("Dépensé mis à jour");
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  }

  if (loading && budgets.length === 0 && obligations.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center py-16" style={{ color: C.dim }}>
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Chargement…
      </div>
    );
  }

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto pb-4 pt-2">
      <p className="text-[11px]" style={{ color: C.muted }}>
        Enveloppes + fiscal + forecast cockpit. Aucun paiement ni transfert auto (DEC-016).
      </p>

      {bSum && fSum ? (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <MiniStat label="Alloué" value={formatCurrency(bSum.total_allocated)} />
          <MiniStat label="Restant budgets" value={formatCurrency(bSum.remaining)} />
          <MiniStat label="Fiscal ouvert" value={formatCurrency(fSum.open_total)} />
          <MiniStat label="Prochaine échéance" value={fSum.next_due ?? "—"} />
        </div>
      ) : null}

      <ForecastCockpitPanel period={period} />

      <BudgetsSection
        budgets={budgets}
        alertsByDept={alertsByDept}
        dept={dept}
        period={period}
        amount={amount}
        saving={saving}
        onDept={setDept}
        onPeriod={setPeriod}
        onAmount={setAmount}
        onAdd={() => void addBudget()}
        onSpent={(id, spent) => void setSpent(id, spent)}
      />

      <FiscalSection
        obligations={obligations}
        title={fiscalTitle}
        amount={fiscalAmount}
        due={fiscalDue}
        kind={fiscalKind}
        saving={saving}
        onTitle={setFiscalTitle}
        onAmount={setFiscalAmount}
        onDue={setFiscalDue}
        onKind={setFiscalKind}
        onAdd={() => void addFiscal()}
        onPaid={(id) => void markPaid(id)}
      />
    </div>
  );
}
