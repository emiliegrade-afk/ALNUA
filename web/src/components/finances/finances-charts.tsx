"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  CATEGORY_LABELS,
  EXPENSE_CATEGORY_COLORS,
  formatMonthLabel,
} from "@/components/finances/finances.constants";
import { Donut } from "@/components/console/charts";
import { formatCurrency } from "@/lib/finances-api";
import type { MonthTotals } from "@/lib/finances-api";
import { C } from "@/app/app-v2/shared";

/* Redesign Vue Globale Finance : chrome cockpit cohérent (C.line, fond
   rgba(16,13,11,.55)) au lieu du Card shadcn d'origine, pour matcher le
   reste de la page. "Revenus vs dépenses" devient "Évolution financière" en
   LineChart 3 séries (Entrées/Sorties/Résultat net) ; le donut remplace le
   PieChart recharts (Donut a déjà centerLabel/centerValue, pas besoin de
   réinventer un label central custom). */

const tooltipStyle = {
  background: "#14171D",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  fontSize: 12,
};

export function FinancesEvolutionChart({ months }: { months: MonthTotals[] }) {
  const data = useMemo(
    () => months.map((m) => ({ ...m, label: formatMonthLabel(m.month) })),
    [months]
  );

  return (
    <div className="rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
      <p className="mb-2.5 text-[10.5px]" style={{ color: "#D8CFC4" }}>
        Évolution financière (6 mois)
      </p>
      {data.length === 0 ? (
        <p className="text-[10.5px]" style={{ color: C.faint }}>
          Pas encore de données.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#ffffff10" strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={{ stroke: "#ffffff15" }} tickLine={false} />
            <YAxis
              tick={{ fill: "#9ca3af", fontSize: 11 }}
              axisLine={{ stroke: "#ffffff15" }}
              tickLine={false}
              width={52}
              tickFormatter={(v) => new Intl.NumberFormat("fr-FR", { notation: "compact", maximumFractionDigits: 0 }).format(v)}
            />
            <Tooltip contentStyle={tooltipStyle} formatter={(value, name) => [formatCurrency(Number(value ?? 0)), String(name)]} />
            <Line type="monotone" dataKey="total_income" name="Entrées" stroke="#7FC98C" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="total_expenses" name="Sorties" stroke="#f87171" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="balance" name="Résultat net" stroke={C.copperLight} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

/** Composition legacy — utilisée par `/finances` (finances-view.tsx), qui
 * reste sur son propre chrome Card shadcn (pas le redesign cockpit). Garder
 * ce composant combiné évite de toucher la page legacy pendant que
 * `/finances-v2` compose les deux panneaux granulaires ci-dessous
 * différemment (nouvelle disposition, chrome cockpit). */
export function FinancesCharts({
  months,
  expenseByCategory,
}: {
  months: MonthTotals[];
  expenseByCategory: Record<string, number>;
}) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <FinancesEvolutionChart months={months} />
      <FinancesExpenseDonut expenseByCategory={expenseByCategory} />
    </div>
  );
}

export function FinancesExpenseDonut({
  expenseByCategory,
  monthLabel,
}: {
  expenseByCategory: Record<string, number>;
  monthLabel?: string;
}) {
  const segments = useMemo(
    () =>
      Object.entries(expenseByCategory)
        .filter(([, v]) => v > 0)
        .sort((a, b) => b[1] - a[1])
        .map(([category, value]) => ({
          category,
          value,
          color: EXPENSE_CATEGORY_COLORS[category as keyof typeof EXPENSE_CATEGORY_COLORS] ?? "#94a3b8",
        })),
    [expenseByCategory]
  );
  const total = segments.reduce((sum, s) => sum + s.value, 0);

  return (
    <div className="rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
      <p className="mb-2.5 text-[10.5px]" style={{ color: "#D8CFC4" }}>
        Dépenses par catégorie{monthLabel ? ` — ${monthLabel}` : ""}
      </p>
      {segments.length === 0 ? (
        <p className="text-[10.5px]" style={{ color: C.faint }}>
          Aucune dépense ce mois.
        </p>
      ) : (
        <div className="flex items-center gap-4">
          <Donut segments={segments} size={104} thickness={12} centerValue={formatCurrency(total)} centerLabel="Total" />
          <div className="flex min-w-0 flex-1 flex-col gap-1.5">
            {segments.map((s) => (
              <div key={s.category} className="flex items-center gap-1.5 text-[9.5px]">
                <span className="h-[7px] w-[7px] shrink-0 rounded-full" style={{ background: s.color }} />
                <span className="min-w-0 flex-1 truncate" style={{ color: C.warm }}>
                  {CATEGORY_LABELS[s.category] ?? s.category}
                </span>
                <span className="shrink-0" style={{ color: C.dim }}>
                  {formatCurrency(s.value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
