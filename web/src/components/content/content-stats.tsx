"use client";

import { Card, CardContent } from "@/components/ui/card";

interface ContentStatsProps {
  pending: number;
  approvedThisWeek: number;
  publishedThisMonth: number;
}

export function ContentStats({
  pending,
  approvedThisWeek,
  publishedThisMonth,
}: ContentStatsProps) {
  const items = [
    { label: "En attente d'approbation", value: pending, accent: "text-copper-glow" },
    { label: "Approuvés cette semaine", value: approvedThisWeek, accent: "text-emerald-400" },
    { label: "Publiés ce mois", value: publishedThisMonth, accent: "text-sky-400" },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {items.map(({ label, value, accent }) => (
        <Card
          key={label}
          className="border-white/[0.06] bg-surface/60 ring-1 ring-copper/10"
        >
          <CardContent className="p-4">
            <p className={`text-2xl font-semibold tabular-nums ${accent}`}>
              {value}
            </p>
            <p className="mt-1 text-[11px] leading-snug text-titanium">
              {label}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
