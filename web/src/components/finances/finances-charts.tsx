"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/finances-api";
import type { MonthTotals } from "@/lib/finances-api";

interface FinancesChartsProps {
  months: MonthTotals[];
  expenseByCategory: Record<string, number>;
}

const tooltipStyle = {
  background: "#14171D",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  fontSize: 12,
};

export function FinancesCharts({ months, expenseByCategory }: FinancesChartsProps) {
  const barData = useMemo(
    () =>
      months.map((m) => ({
        ...m,
        label: formatMonthLabel(m.month),
      })),
    [months]
  );

  const donutData = useMemo(
    () =>
      Object.entries(expenseByCategory)
        .filter(([, v]) => v > 0)
        .map(([category, value]) => ({
          name: CATEGORY_LABELS[category] ?? category,
          value,
          category,
        })),
    [expenseByCategory]
  );

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="border-white/10 bg-surface/80">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-ivory">
            Revenus vs dépenses (6 mois)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {barData.length === 0 ? (
            <p className="text-sm text-titanium">Pas encore de données.</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#ffffff10" strokeDasharray="3 3" />
                <XAxis
                  dataKey="label"
                  tick={{ fill: "#9ca3af", fontSize: 11 }}
                  axisLine={{ stroke: "#ffffff15" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#9ca3af", fontSize: 11 }}
                  axisLine={{ stroke: "#ffffff15" }}
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
                <Bar
                  dataKey="total_income"
                  name="Revenus"
                  fill="#34d399"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={32}
                />
                <Bar
                  dataKey="total_expenses"
                  name="Dépenses"
                  fill="#f87171"
                  fillOpacity={0.85}
                  radius={[4, 4, 0, 0]}
                  maxBarSize={32}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Card className="border-white/10 bg-surface/80">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-ivory">
            Dépenses par catégorie
          </CardTitle>
        </CardHeader>
        <CardContent>
          {donutData.length === 0 ? (
            <p className="text-sm text-titanium">Aucune dépense ce mois.</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={donutData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={2}
                >
                  {donutData.map((entry) => (
                    <Cell
                      key={entry.category}
                      fill={
                        EXPENSE_CATEGORY_COLORS[
                          entry.category as keyof typeof EXPENSE_CATEGORY_COLORS
                        ] ?? "#94a3b8"
                      }
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value) => formatCurrency(Number(value ?? 0))}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
