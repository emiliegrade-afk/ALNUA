"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { WaitlistStats } from "@/lib/waitlist-api";
import { cn } from "@/lib/utils";

interface WaitlistKpiCardsProps {
  stats: WaitlistStats;
  selectedProjectId: string;
  onSelectProject: (projectId: string) => void;
}

export function WaitlistKpiCards({
  stats,
  selectedProjectId,
  onSelectProject,
}: WaitlistKpiCardsProps) {
  const cards = stats.per_project.filter((p) => p.total > 0 || stats.per_project.length <= 4);

  if (cards.length === 0) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {stats.per_project.slice(0, 3).map((p) => (
          <Card
            key={p.project_id}
            className={cn(
              "cursor-pointer border-white/10 bg-surface/80 transition hover:border-copper/30",
              selectedProjectId === p.project_id && "border-copper/45 ring-1 ring-copper/20"
            )}
            onClick={() => onSelectProject(p.project_id)}
          >
            <CardContent className="p-4">
              <p className="text-sm font-medium text-ivory">{p.project_name}</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums text-copper-glow">
                {p.total}
              </p>
              <p className="mt-1 text-xs text-titanium">inscrites</p>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <Card
        className={cn(
          "cursor-pointer border-white/10 bg-surface/80 transition hover:border-copper/30",
          selectedProjectId === "all" && "border-copper/45 ring-1 ring-copper/20"
        )}
        onClick={() => onSelectProject("all")}
      >
        <CardContent className="p-4">
          <p className="text-sm font-medium text-ivory">Tous les projets</p>
          <p className="mt-2 text-2xl font-semibold tabular-nums text-copper-glow">
            {stats.total}
          </p>
          {stats.this_week > 0 ? (
            <Badge variant="outline" className="mt-2 border-emerald-500/30 text-emerald-300">
              +{stats.this_week} cette semaine
            </Badge>
          ) : (
            <p className="mt-1 text-xs text-titanium">inscrites au total</p>
          )}
        </CardContent>
      </Card>

      {stats.per_project.map((p) => (
        <Card
          key={p.project_id}
          className={cn(
            "cursor-pointer border-white/10 bg-surface/80 transition hover:border-copper/30",
            selectedProjectId === p.project_id && "border-copper/45 ring-1 ring-copper/20"
          )}
          onClick={() => onSelectProject(p.project_id)}
        >
          <CardContent className="p-4">
            <p className="text-sm font-medium text-ivory">{p.project_name}</p>
            <p className="mt-2 text-2xl font-semibold tabular-nums text-copper-glow">
              {p.total}
            </p>
            {p.this_week > 0 ? (
              <Badge variant="outline" className="mt-2 border-emerald-500/30 text-emerald-300">
                +{p.this_week} cette semaine
              </Badge>
            ) : (
              <p className="mt-1 text-xs text-titanium">inscrites</p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
