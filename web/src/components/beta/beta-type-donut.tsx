"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { BETA_TYPE_LABELS } from "@/components/beta/beta.constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const COLORS = ["#C08A72", "#22c55e", "#f59e0b", "#06b6d4", "#a78bfa"];

interface BetaTypeDonutProps {
  byType: Record<string, number>;
  compact?: boolean;
}

export function BetaTypeDonut({ byType, compact }: BetaTypeDonutProps) {
  const data = Object.entries(byType).map(([type, count]) => ({
    name: BETA_TYPE_LABELS[type] ?? type,
    value: count,
  }));

  if (data.length === 0) {
    return (
      <Card className="border-white/10 bg-surface/80">
        <CardHeader className={compact ? "pb-2" : undefined}>
          <CardTitle className="text-sm font-medium text-ivory">
            Par type
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-titanium">Aucun feedback</CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-white/10 bg-surface/80">
      <CardHeader className={compact ? "pb-0" : undefined}>
        <CardTitle className="text-sm font-medium text-ivory">Par type</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={compact ? 140 : 220}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={compact ? 35 : 50}
              outerRadius={compact ? 55 : 80}
              paddingAngle={2}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "#14171D",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 8,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
