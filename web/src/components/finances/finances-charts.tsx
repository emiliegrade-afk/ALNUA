"use client";

import { useId, useMemo } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
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

const PANEL = "finance-instrument flex h-full flex-col p-4";

const SERIES = [
  { key: "total_income", name: "Entrées", color: "#3DDC97" },
  { key: "total_expenses", name: "Sorties", color: "#F87171" },
  { key: "balance", name: "Profit", color: "#E09B6A" },
] as const;

const tooltipStyle = {
  background: "rgba(0,0,0,0.92)",
  border: "1px solid rgba(167,173,181,0.28)",
  borderRadius: 2,
  fontSize: 11,
  color: "#F5F2EA",
};

function ChartGlowDefs({
  uid,
  colors,
}: {
  uid: string;
  colors: readonly { key: string; color: string }[];
}) {
  return (
    <defs>
      {colors.map((s) => (
        <filter
          key={s.key}
          id={`glow-${uid}-${s.key}`}
          x="-50%"
          y="-50%"
          width="200%"
          height="200%"
        >
          <feGaussianBlur stdDeviation="3.8" result="blur" />
          <feFlood floodColor={s.color} floodOpacity="0.6" result="color" />
          <feComposite in="color" in2="blur" operator="in" result="glow" />
          <feMerge>
            <feMergeNode in="glow" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      ))}
      {colors.map((s) => (
        <linearGradient
          key={`g-${s.key}`}
          id={`area-${uid}-${s.key}`}
          x1="0"
          y1="0"
          x2="0"
          y2="1"
        >
          <stop offset="0%" stopColor={s.color} stopOpacity={0.14} />
          <stop offset="100%" stopColor={s.color} stopOpacity={0} />
        </linearGradient>
      ))}
    </defs>
  );
}

export function FinancesEvolutionChart({ months }: { months: MonthTotals[] }) {
  const uid = useId().replace(/:/g, "");
  const data = useMemo(
    () => months.map((m) => ({ ...m, label: formatMonthLabel(m.month) })),
    [months],
  );

  return (
    <div className={PANEL}>
      <h3 className="mb-2 text-[9px] font-medium uppercase tracking-[0.24em] text-titanium">
        Évolution financière
      </h3>
      {data.length === 0 ? (
        <p className="text-sm text-titanium/50">Pas encore de données.</p>
      ) : (
        <div className="relative min-h-[240px] flex-1">
          <ResponsiveContainer width="100%" height="100%" minHeight={240}>
            <ComposedChart data={data} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
              <ChartGlowDefs uid={uid} colors={SERIES} />
              <CartesianGrid
                stroke="rgba(167,173,181,0.07)"
                strokeDasharray="1 8"
                vertical={false}
              />
              <XAxis
                dataKey="label"
                tick={{ fill: "#6D737C", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#6D737C", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                width={40}
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
                cursor={{ stroke: "rgba(167,173,181,0.2)", strokeWidth: 1 }}
              />
              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ fontSize: 9, top: -2, color: "#A7ADB5" }}
                iconType="circle"
                iconSize={6}
              />
              {SERIES.map((s) => (
                <Area
                  key={`area-${s.key}`}
                  type="monotone"
                  dataKey={s.key}
                  stroke="none"
                  fill={`url(#area-${uid}-${s.key})`}
                  fillOpacity={1}
                  legendType="none"
                  tooltipType="none"
                  isAnimationActive={false}
                />
              ))}
              {SERIES.map((s) => (
                <Line
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.name}
                  stroke={s.color}
                  strokeWidth={1.75}
                  filter={`url(#glow-${uid}-${s.key})`}
                  dot={false}
                  activeDot={{ r: 3.5, fill: s.color, strokeWidth: 0 }}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
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
            ] ?? "#A7ADB5",
        })),
    [expenseByCategory],
  );
  const total = segments.reduce((sum, s) => sum + s.value, 0);

  return (
    <div className={PANEL}>
      <h3 className="mb-2 text-[9px] font-medium uppercase tracking-[0.24em] text-titanium">
        Dépenses{monthLabel ? ` · ${monthLabel}` : ""}
      </h3>
      {segments.length === 0 ? (
        <p className="text-sm text-titanium/50">Aucune dépense ce mois.</p>
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 pt-1">
          <Donut
            segments={segments}
            size={118}
            thickness={12}
            centerValue={formatCurrency(total)}
            centerLabel="Total"
          />
          <ul className="flex w-full flex-col gap-1.5 text-[10px]">
            {segments.slice(0, 4).map((s) => {
              const pct = total > 0 ? Math.round((s.value / total) * 100) : 0;
              return (
                <li
                  key={s.category}
                  className="flex items-center justify-between gap-2"
                >
                  <span className="flex min-w-0 items-center gap-1.5 text-titanium">
                    <span
                      className="h-1 w-1 shrink-0 rounded-full"
                      style={{ background: s.color }}
                    />
                    <span className="truncate">
                      {CATEGORY_LABELS[s.category] ?? s.category}
                    </span>
                  </span>
                  <span className="shrink-0 tabular-nums text-titanium/70">{pct}%</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
