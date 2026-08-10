"use client";

import { Plus } from "lucide-react";
import {
  formatCurrency,
  type BudgetAlertSeverity,
  type BudgetDepartmentAlert,
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

export const FISCAL_KINDS = [
  "tva",
  "urssaf",
  "impot",
  "cfe",
  "retraite",
  "assurance",
  "autre",
] as const;

const ALERT_STYLE: Record<BudgetAlertSeverity, { bg: string; color: string; label: string }> = {
  ok: { bg: "rgba(61,220,151,.12)", color: "#3DDC97", label: "OK" },
  warning: { bg: "rgba(224,155,106,.15)", color: "#E09B6A", label: "80%+" },
  critical: { bg: "rgba(248,113,113,.15)", color: "#F87171", label: "Dépassé" },
};

export function BudgetAlertBadge({ severity }: { severity: BudgetAlertSeverity }) {
  const s = ALERT_STYLE[severity];
  return (
    <span
      className="rounded px-1.5 py-px text-[9px] font-medium uppercase tracking-wide"
      style={{ background: s.bg, color: s.color }}
    >
      {s.label}
    </span>
  );
}

export function MiniStat({ label, value }: { label: string; value: string }) {
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

type BudgetsSectionProps = {
  budgets: FinanceBudget[];
  alertsByDept: Record<string, BudgetDepartmentAlert>;
  dept: string;
  period: string;
  amount: string;
  saving: boolean;
  onDept: (v: string) => void;
  onPeriod: (v: string) => void;
  onAmount: (v: string) => void;
  onAdd: () => void;
  onSpent: (id: string, spent: number) => void;
};

export function BudgetsSection(p: BudgetsSectionProps) {
  return (
    <section className="rounded-xl border p-3" style={{ borderColor: C.line }}>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-[12px] font-medium" style={{ color: C.ivory }}>
          Budgets
        </h3>
        <span className="text-[10px]" style={{ color: C.faint }}>
          {p.budgets.length} enveloppe(s)
        </span>
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        <select
          value={p.dept}
          onChange={(e) => p.onDept(e.target.value)}
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
          value={p.period}
          onChange={(e) => p.onPeriod(e.target.value)}
          placeholder="2026-08"
          className="w-24 rounded-md border bg-transparent px-2 py-1 text-[11px]"
          style={{ borderColor: C.line, color: C.ivory }}
        />
        <input
          value={p.amount}
          onChange={(e) => p.onAmount(e.target.value)}
          placeholder="Montant"
          type="number"
          min={0}
          className="w-28 rounded-md border bg-transparent px-2 py-1 text-[11px]"
          style={{ borderColor: C.line, color: C.ivory }}
        />
        <button
          type="button"
          disabled={p.saving}
          onClick={p.onAdd}
          className="flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px]"
          style={{ borderColor: "rgba(224,155,106,.4)", color: C.copperLight }}
        >
          <Plus className="h-3 w-3" /> Ajouter
        </button>
      </div>
      <ul className="space-y-1.5">
        {p.budgets.length === 0 ? (
          <li className="text-[11px]" style={{ color: C.faint }}>
            Aucune enveloppe — crée la première pour Marketing / App / …
          </li>
        ) : (
          p.budgets.map((b) => {
            const alert = p.alertsByDept[b.department];
            const util = b.utilization_pct ?? 0;
            return (
            <li
              key={b.id}
              className="flex items-center justify-between gap-2 rounded-lg border px-2.5 py-1.5 text-[11px]"
              style={{ borderColor: C.lineSoft }}
            >
              <span className="flex items-center gap-1.5" style={{ color: C.ivory }}>
                {b.department} · {b.period}
                {alert ? <BudgetAlertBadge severity={alert.severity} /> : null}
                <span className="ml-1" style={{ color: C.faint }}>
                  {b.label}
                </span>
              </span>
              <span className="flex shrink-0 items-center gap-2" style={{ color: C.warm }}>
                {formatCurrency(b.amount, b.currency)}
                <span style={{ color: C.faint }}>
                  {util.toFixed(0)}%
                </span>
                <button
                  type="button"
                  onClick={() => p.onSpent(b.id, b.spent_manual ?? b.spent ?? 0)}
                  className="rounded border px-1.5 py-px text-[9px]"
                  style={{ borderColor: C.line, color: C.dim }}
                  title={
                    b.spent_computed != null
                      ? `Calculé: ${formatCurrency(b.spent_computed, b.currency)}`
                      : undefined
                  }
                >
                  dépensé {formatCurrency(b.spent ?? 0, b.currency)}
                </button>
              </span>
            </li>
            );
          })
        )}
      </ul>
    </section>
  );
}

type FiscalSectionProps = {
  obligations: FiscalObligation[];
  title: string;
  amount: string;
  due: string;
  kind: string;
  saving: boolean;
  onTitle: (v: string) => void;
  onAmount: (v: string) => void;
  onDue: (v: string) => void;
  onKind: (v: string) => void;
  onAdd: () => void;
  onPaid: (id: string) => void;
};

export function FiscalSection(p: FiscalSectionProps) {
  return (
    <section className="rounded-xl border p-3" style={{ borderColor: C.line }}>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-[12px] font-medium" style={{ color: C.ivory }}>
          Obligations fiscales
        </h3>
        <span className="text-[10px]" style={{ color: C.faint }}>
          {p.obligations.length} ligne(s)
        </span>
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        <input
          value={p.title}
          onChange={(e) => p.onTitle(e.target.value)}
          placeholder="Ex. TVA T2"
          className="min-w-[120px] flex-1 rounded-md border bg-transparent px-2 py-1 text-[11px]"
          style={{ borderColor: C.line, color: C.ivory }}
        />
        <select
          value={p.kind}
          onChange={(e) => p.onKind(e.target.value)}
          className="rounded-md border bg-transparent px-2 py-1 text-[11px]"
          style={{ borderColor: C.line, color: C.ivory }}
        >
          {FISCAL_KINDS.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={p.due}
          onChange={(e) => p.onDue(e.target.value)}
          className="rounded-md border bg-transparent px-2 py-1 text-[11px]"
          style={{ borderColor: C.line, color: C.ivory }}
        />
        <input
          value={p.amount}
          onChange={(e) => p.onAmount(e.target.value)}
          placeholder="Montant"
          type="number"
          min={0}
          className="w-24 rounded-md border bg-transparent px-2 py-1 text-[11px]"
          style={{ borderColor: C.line, color: C.ivory }}
        />
        <button
          type="button"
          disabled={p.saving}
          onClick={p.onAdd}
          className="flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px]"
          style={{ borderColor: "rgba(224,155,106,.4)", color: C.copperLight }}
        >
          <Plus className="h-3 w-3" /> Ajouter
        </button>
      </div>
      <ul className="space-y-1.5">
        {p.obligations.length === 0 ? (
          <li className="text-[11px]" style={{ color: C.faint }}>
            Aucune échéance — TVA, URSSAF… (paiement externe).
          </li>
        ) : (
          p.obligations.map((o) => (
            <li
              key={o.id}
              className="flex items-center justify-between gap-2 rounded-lg border px-2.5 py-1.5 text-[11px]"
              style={{ borderColor: C.lineSoft }}
            >
              <span style={{ color: C.ivory }}>
                {o.title}
                <span className="ml-2" style={{ color: C.faint }}>
                  {o.kind} · {o.due_date} · {STATUS_LABEL[o.status] ?? o.status}
                </span>
              </span>
              <span className="flex shrink-0 items-center gap-2">
                <span style={{ color: C.warm }}>{formatCurrency(o.amount, o.currency)}</span>
                {o.status !== "paid_externally" && o.status !== "cancelled" ? (
                  <button
                    type="button"
                    onClick={() => p.onPaid(o.id)}
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
  );
}
