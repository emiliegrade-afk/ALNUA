"use client";

import {
  PERIOD_OPTIONS,
} from "@/components/analytics/analytics.constants";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AnalyticsPeriod } from "@/lib/analytics";
import { getProjectAccent } from "@/lib/projects";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AnalyticsFiltersProps {
  period: AnalyticsPeriod;
  onPeriodChange: (period: AnalyticsPeriod) => void;
  projectFilter: string;
  onProjectFilterChange: (value: string) => void;
  projects: Project[];
}

export function AnalyticsFilters({
  period,
  onPeriodChange,
  projectFilter,
  onProjectFilterChange,
  projects,
}: AnalyticsFiltersProps) {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-copper/10 bg-obsidian/50 p-4 ring-1 ring-white/[0.04] sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap gap-1.5">
        {PERIOD_OPTIONS.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => onPeriodChange(id)}
            className={cn(
              "rounded-lg border px-3 py-1.5 text-xs transition",
              period === id
                ? "border-copper/45 bg-copper/10 text-copper-glow"
                : "border-transparent text-titanium hover:border-copper/20 hover:bg-white/[0.03]"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <Select value={projectFilter} onValueChange={onProjectFilterChange}>
        <SelectTrigger className="w-full border-copper/20 bg-obsidian sm:w-[220px]">
          <SelectValue placeholder="Projet" />
        </SelectTrigger>
        <SelectContent className="border-copper/20 bg-surface-raised">
          <SelectItem value="all">Tous les projets</SelectItem>
          {projects.map((p) => {
            const accent = getProjectAccent(p.branch);
            return (
              <SelectItem key={p.id} value={p.id}>
                <span className="flex items-center gap-2">
                  <span className={cn("h-1.5 w-1.5 rounded-full", accent.dot)} />
                  {p.name}
                </span>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
    </div>
  );
}
