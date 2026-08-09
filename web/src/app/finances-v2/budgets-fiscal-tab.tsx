"use client";

import { useEffect, useState } from "react";
import { Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import {
  createFinanceBudget,
  createFiscalObligation,
  fetchFinanceBudgets,
  fetchFiscalObligations,
  formatCurrency,
  updateFiscalObligation,
  type FinanceBudget,
  type FiscalObligation,
  type FiscalStatus,
} from "@/lib/finances-api";
import { C } from "../app-v2/shared";

const STATUS_LABEL: Record<FiscalStatus, string> = {
  upcoming: "À venir",
  due: "Échéance",
  paid_externally: "Payée (externe)",
  cancelled: "Annulée",
};

export function BudgetsFiscalTab() {
  const [budgets, setBudgets] = useState<FinanceBudget[]>([]);
  const [obligations, setObligations] = useState<FiscalObligation[]>([]);
  const [loading, setLoading] = useState(true);
  const [dept, setDept] = useState("marketing");
  const [period, setPeriod] = useState(() => new Date().toISOString().slice(0, 7));
  const [amount, setAmount] = useState("");
  const [fiscalTitle, setFiscalTitle] = useState("");
  const [fiscalAmount, setFiscalAmount] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [b, f] = await Promise.all([fetchFinanceBudgets(), fetchFiscalObligations()]);
      setBudgets(b.budgets);
      setObligations(f.obligations);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Chargement budgets/fiscal impossible");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function addBudget() {
    const value = parseFloat(amount);
    if (!dept.trim() || Number.isNaN(value) || value < 0) return;
    setSaving(true);
    try {
      await createFinanceBudget({ department: dept.trim(), period, amount: value });
      toast.success("Enveloppe budget créée (pas de transfert auto).");
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
        status: "upcoming",
        kind: "autre",
      });
      toast.success("Obligation fiscale ajoutée (paiement hors Hub).");
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
        Enveloppes par département + échéances fiscales. Aucun paiement ni transfert automatique
        (DEC-016 / Vague 3).
      </p>

      <section className="rounded-xl border p-3" style={{ borderColor: C.line }}>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-[12px] font-medium" style={{ color: C.ivory }}>
            Budgets
          </h3>
          <span className="text-[10px]" style={{ color: C.faint }}>
            {budgets.length} enveloppe(s)
          </span>
        </div>
        <div className="mb-3 flex flex-wrap gap-2">
          <select
            value={dept}
            onChange={(e) => setDept(e.target.value)}
            className="rounded-md border bg-transparent px-2 py-1 text-[11px]"
            style={{ borderColor: C.line, color: C.ivory }}
          >
            {["app", "gaming", "robo", "marketing", "rnd", "finances", "company", "other"].map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <input
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            placeholder="2026-08"
            className="w-24 rounded-md border bg-transparent px-2 py-1 text-[11px]"
            style={{ borderColor: C.line, color: C.ivory }}
          />
          <input
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="Montant"
            type="number"
            min={0}
            className="w-28 rounded-md border bg-transparent px-2 py-1 text-[11px]"
            style={{ borderColor: C.line, color: C.ivory }}
          />
          <button
            type="button"
            disabled={saving}
            onClick={() => void addBudget()}
            className="flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px]"
            style={{ borderColor: "rgba(192,138,114,.4)", color: C.copperLight }}
          >
            <Plus className="h-3 w-3" /> Ajouter
          </button>
        </div>
        <ul className="space-y-1.5">
          {budgets.length === 0 ? (
            <li className="text-[11px]" style={{ color: C.faint }}>
              Aucune enveloppe — crée la première pour suivre Marketing / App / …
            </li>
          ) : (
            budgets.map((b) => (
              <li
                key={b.id}
                className="flex items-center justify-between rounded-lg border px-2.5 py-1.5 text-[11px]"
                style={{ borderColor: C.lineSoft }}
              >
                <span style={{ color: C.ivory }}>
                  {b.department} · {b.period}
                  <span className="ml-2" style={{ color: C.faint }}>
                    {b.label}
                  </span>
                </span>
                <span style={{ color: C.warm }}>
                  {formatCurrency(b.amount, b.currency)}
                  <span className="ml-2" style={{ color: C.faint }}>
                    dépensé {formatCurrency(b.spent ?? 0, b.currency)}
                  </span>
                </span>
              </li>
            ))
          )}
        </ul>
      </section>

      <section className="rounded-xl border p-3" style={{ borderColor: C.line }}>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-[12px] font-medium" style={{ color: C.ivory }}>
            Obligations fiscales
          </h3>
          <span className="text-[10px]" style={{ color: C.faint }}>
            {obligations.length} ligne(s)
          </span>
        </div>
        <div className="mb-3 flex flex-wrap gap-2">
          <input
            value={fiscalTitle}
            onChange={(e) => setFiscalTitle(e.target.value)}
            placeholder="Ex. TVA T2"
            className="min-w-[140px] flex-1 rounded-md border bg-transparent px-2 py-1 text-[11px]"
            style={{ borderColor: C.line, color: C.ivory }}
          />
          <input
            value={fiscalAmount}
            onChange={(e) => setFiscalAmount(e.target.value)}
            placeholder="Montant"
            type="number"
            min={0}
            className="w-28 rounded-md border bg-transparent px-2 py-1 text-[11px]"
            style={{ borderColor: C.line, color: C.ivory }}
          />
          <button
            type="button"
            disabled={saving}
            onClick={() => void addFiscal()}
            className="flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px]"
            style={{ borderColor: "rgba(192,138,114,.4)", color: C.copperLight }}
          >
            <Plus className="h-3 w-3" /> Ajouter
          </button>
        </div>
        <ul className="space-y-1.5">
          {obligations.length === 0 ? (
            <li className="text-[11px]" style={{ color: C.faint }}>
              Aucune échéance — TVA, URSSAF, etc. (paiement externe uniquement).
            </li>
          ) : (
            obligations.map((o) => (
              <li
                key={o.id}
                className="flex items-center justify-between gap-2 rounded-lg border px-2.5 py-1.5 text-[11px]"
                style={{ borderColor: C.lineSoft }}
              >
                <span style={{ color: C.ivory }}>
                  {o.title}
                  <span className="ml-2" style={{ color: C.faint }}>
                    {o.due_date} · {STATUS_LABEL[o.status] ?? o.status}
                  </span>
                </span>
                <span className="flex shrink-0 items-center gap-2">
                  <span style={{ color: C.warm }}>{formatCurrency(o.amount, o.currency)}</span>
                  {o.status !== "paid_externally" && o.status !== "cancelled" ? (
                    <button
                      type="button"
                      onClick={() => void markPaid(o.id)}
                      className="rounded border px-1.5 py-px text-[9px]"
                      style={{ borderColor: C.line, color: C.dim }}
                    >
                      Payée externe
                    </button>
                  ) : null}
                </span>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  );
}
