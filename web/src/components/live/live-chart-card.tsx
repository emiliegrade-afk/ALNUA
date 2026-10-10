"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { ChartSeries } from "@/lib/live-cards";

export function LiveChartCard({ series }: { series: ChartSeries }) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-copper-light">{series.title}</p>
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={series.points} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <XAxis dataKey="label" tick={{ fill: "#c4b5a0", fontSize: 11 }} />
            <YAxis tick={{ fill: "#c4b5a0", fontSize: 11 }} width={32} />
            <Tooltip
              contentStyle={{ background: "#1a1612", border: "1px solid #c4a574", color: "#f4efe6" }}
            />
            <Bar dataKey="value" fill="#c4a574" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
