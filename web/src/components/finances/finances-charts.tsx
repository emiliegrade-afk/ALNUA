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

const tooltipStyle = {
  background: "#16181D",
  border: "1px solid #23262F",
  borderRadius: 8,
  fontSize: 12,
  color: "#F5F2EA",
};

export function FinancesEvolutionChart({ months }: { months: MonthTotals[] }) {
  const data = useMemo(
    () => months.map((m) => ({ ...m, label: formatMonthLabel(m.month) })),
    [months],
  );

  return (
    <div className="rounded-xl border border-alnua-border bg-alnua-surface p-5">
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-alnua-titane">
        Évolution financière
      </h3>
      {data.length === 0 ? (
        <p className="text-sm text-alnua-titane">Pas encore de données.</p>
      ) : (
        <ResponsiveContainer width="100%" height={256}>
          <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#23262F80" strokeDasharray="3 3" />
            <XAxis
              dataKey="label"
              tick={{ fill: "#A7AD85", fontSize: 11 }}
              axisLine={{ stroke: "#23262F" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#A7AD85", fontSize: 11 }}
              axisLine={{ stroke: "#23262F" }}
              tickLine={false}
              width={52}
              tickFormatter={(v) =>
                new Intl.NumberFormat("fr-FR", {
                  notation: "compact",
                  maximumFractionDigits: 0,
                }).format(v)
              }
            />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value, name) => [
                formatCurrency(Number(value ?? 0)),
                String(name),
              ]}
            />
            <Line
              type="monotone"
              dataKey="total_income"
              name="Entrées"
              stroke="#2DD4BF"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="total_expenses"
              name="Sorties"
              stroke="#F87171"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="balance"
              name="Résultat net"
              stroke="#C08A72"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
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
          color:
            EXPENSE_CATEGORY_COLORS[
              category as keyof typeof EXPENSE_CATEGORY_COLORS
            ] ?? "#A7AD85",
        })),
    [expenseByCategory],
  );
  const total = segments.reduce((sum, s) => sum + s.value, 0);

  return (
    <div className="rounded-xl border border-alnua-border bg-alnua-surface p-5">
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-alnua-titane">
        Répartition des dépenses
        {monthLabel ? ` — ${monthLabel}` : ""}
      </h3>
      {segments.length === 0 ? (
        <p className="text-sm text-alnua-titane">Aucune dépense ce mois.</p>
      ) : (
        <div className="mt-4 flex items-center gap-6">
          <Donut
            segments={segments}
            size={128}
            thickness={16}
            centerValue={formatCurrency(total)}
            centerLabel="Total"
          />
          <ul className="flex flex-1 flex-col gap-3 text-xs">
            {segments.map((s) => {
              const pct = total > 0 ? Math.round((s.value / total) * 100) : 0;
              return (
                <li
                  key={s.category}
                  className="flex items-center justify-between gap-2"
                >
                  <span className="flex min-w-0 items-center gap-2 text-alnua-ivoire">
                    <span
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ background: s.color }}
                    />
                    <span className="truncate">
                      {CATEGORY_LABELS[s.category] ?? s.category}
                    </span>
                  </span>
                  <span className="shrink-0 text-alnua-titane">{pct}%</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
