"use client";

import { useMemo } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartEmptyState } from "@/components/analytics/chart-empty-state";
import {
  CHART_COLORS,
  formatMonthLabel,
} from "@/components/analytics/analytics.constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RevenueMonth } from "@/lib/analytics";

interface RevenueChartProps {
  months: RevenueMonth[];
  onAddMetric?: () => void;
}

export function RevenueChart({ months, onAddMetric }: RevenueChartProps) {
  const data = useMemo(
    () =>
      months.map((m) => ({
        ...m,
        label: formatMonthLabel(m.month),
      })),
    [months]
  );

  const empty =
    months.length === 0 ||
    months.every((m) => m.revenue === 0 && m.expense === 0 && m.mrr === 0);

  return (
    <Card className="border-copper/10 bg-surface/80">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-ivory">
          Revenus &amp; Dépenses
        </CardTitle>
      </CardHeader>
      <CardContent>
        {empty ? (
          <ChartEmptyState onAddMetric={onAddMetric} compact />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#ffffff10" strokeDasharray="3 3" />
              <XAxis
                dataKey="label"
                tick={{ fill: "#9ca3af", fontSize: 11 }}
                axisLine={{ stroke: "#ffffff15" }}
                tickLine={false}
              />
              <YAxis
                yAxisId="left"
                tick={{ fill: "#9ca3af", fontSize: 11 }}
                axisLine={{ stroke: "#ffffff15" }}
                tickLine={false}
                width={52}
                tickFormatter={(v) =>
                  new Intl.NumberFormat("fr-FR", {
                    notation: "compact",
                    maximumFractionDigits: 1,
                  }).format(v)
                }
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fill: "#9ca3af", fontSize: 11 }}
                axisLine={{ stroke: "#ffffff15" }}
                tickLine={false}
                width={48}
                tickFormatter={(v) =>
                  new Intl.NumberFormat("fr-FR", {
                    notation: "compact",
                    maximumFractionDigits: 1,
                  }).format(v)
                }
              />
              <Tooltip
                contentStyle={{
                  background: "#141414",
                  border: "1px solid rgba(192,138,114,0.25)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value, name) => [
                  new Intl.NumberFormat("fr-FR", {
                    style: "currency",
                    currency: "EUR",
                    maximumFractionDigits: 0,
                  }).format(Number(value ?? 0)),
                  String(name),
                ]}
              />
              <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
              <Bar
                yAxisId="left"
                dataKey="revenue"
                name="Revenus"
                fill={CHART_COLORS.revenue}
                radius={[4, 4, 0, 0]}
                maxBarSize={36}
              />
              <Bar
                yAxisId="left"
                dataKey="expense"
                name="Dépenses"
                fill={CHART_COLORS.expense}
                fillOpacity={0.75}
                radius={[4, 4, 0, 0]}
                maxBarSize={36}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="mrr"
                name="MRR"
                stroke={CHART_COLORS.mrr}
                strokeWidth={2}
                dot={{ r: 3, fill: CHART_COLORS.mrr }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
