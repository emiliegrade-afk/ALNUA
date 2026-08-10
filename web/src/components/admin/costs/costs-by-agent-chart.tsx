"use client";

import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function CostsByAgentChart({
  byAgent,
}: {
  byAgent: Record<
    string,
    { calls: number; cost_usd: number; prompt_tokens: number; completion_tokens: number }
  >;
}) {
  const data = Object.entries(byAgent)
    .map(([agent, info]) => ({
      agent,
      cost: info.cost_usd,
      calls: info.calls,
    }))
    .sort((a, b) => b.cost - a.cost)
    .slice(0, 12);

  if (data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
        <XAxis
          dataKey="agent"
          tick={{ fill: "#9ca3af", fontSize: 11 }}
          angle={-35}
          textAnchor="end"
          height={60}
        />
        <YAxis
          tick={{ fill: "#9ca3af", fontSize: 11 }}
          tickFormatter={(v: number) => `$${v}`}
        />
        <Tooltip
          contentStyle={{
            background: "#1a1a1f",
            border: "1px solid rgba(224,155,106,0.3)",
            borderRadius: 8,
          }}
          formatter={(value) => {
            const n = typeof value === "number" ? value : Number(value ?? 0);
            return [`$${n.toFixed(4)}`, "Coût"];
          }}
        />
        <Bar dataKey="cost" fill="rgba(224,155,106,0.75)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
