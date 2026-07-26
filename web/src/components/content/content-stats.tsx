"use client";

import { Card, CardContent } from "@/components/ui/card";
import { SECTORS, SECTOR_STYLES } from "@/components/content/content.constants";
import type { Post } from "@/lib/content";
import { cn } from "@/lib/utils";

interface ContentStatsProps {
  pending: number;
  approvedThisWeek: number;
  publishedThisMonth: number;
  posts?: Post[];
}

export function ContentStats({
  pending,
  approvedThisWeek,
  publishedThisMonth,
  posts = [],
}: ContentStatsProps) {
  const items = [
    { label: "En attente d'approbation", value: pending, accent: "text-copper-glow" },
    { label: "Approuvés cette semaine", value: approvedThisWeek, accent: "text-emerald-400" },
    { label: "Publiés ce mois", value: publishedThisMonth, accent: "text-sky-400" },
  ];

  return (
    <div className="space-y-3">
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

      <div className="flex flex-wrap gap-1.5">
        {SECTORS.map(({ id, label }) => {
          const count = posts.filter((p) => p.sector === id).length;
          return (
            <span
              key={id}
              className={cn(
                "rounded-full px-2.5 py-1 text-[10px] ring-1",
                SECTOR_STYLES[id]
              )}
            >
              {label} · {count}
            </span>
          );
        })}
      </div>
    </div>
  );
}
