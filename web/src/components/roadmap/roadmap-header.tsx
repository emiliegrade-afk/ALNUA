"use client";

import { Download, GanttChart, KanbanSquare, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ROADMAP_PRIORITIES,
  type RoadmapViewMode,
} from "@/components/roadmap/roadmap.constants";
import { getProjectAccent } from "@/lib/projects";
import type { RoadmapPriority } from "@/lib/types";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface RoadmapHeaderProps {
  projects: Project[];
  projectFilter: string[];
  onProjectFilterChange: (ids: string[]) => void;
  priorityFilter: RoadmapPriority[];
  onPriorityFilterChange: (priorities: RoadmapPriority[]) => void;
  phaseFilter: string;
  onPhaseFilterChange: (phase: string) => void;
  phases: string[];
  viewMode: RoadmapViewMode;
  onViewModeChange: (mode: RoadmapViewMode) => void;
  itemCount: number;
  onExportCsv: () => void;
  onAddItem: () => void;
}

function FilterChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-lg border px-2.5 py-1 text-[11px] transition",
        active
          ? "border-copper/40 bg-copper/15 text-copper-glow"
          : "border-copper/15 text-titanium hover:border-copper/20"
      )}
    >
      {label}
    </button>
  );
}

export function RoadmapHeader({
  projects,
  projectFilter,
  onProjectFilterChange,
  priorityFilter,
  onPriorityFilterChange,
  phaseFilter,
  onPhaseFilterChange,
  phases,
  viewMode,
  onViewModeChange,
  itemCount,
  onExportCsv,
  onAddItem,
}: RoadmapHeaderProps) {
  function toggleProject(id: string) {
    onProjectFilterChange(
      projectFilter.includes(id)
        ? projectFilter.filter((p) => p !== id)
        : [...projectFilter, id]
    );
  }

  function togglePriority(id: RoadmapPriority) {
    onPriorityFilterChange(
      priorityFilter.includes(id)
        ? priorityFilter.filter((p) => p !== id)
        : [...priorityFilter, id]
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="forge-heading text-[11px] text-copper/80">Planning</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-wide text-ivory">
            Roadmap
          </h1>
          <p className="mt-1 text-sm text-titanium">
            {itemCount} item{itemCount > 1 ? "s" : ""} · 3 projets ALNUA
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-lg border border-copper/15 p-0.5">
            <button
              type="button"
              onClick={() => onViewModeChange("kanban")}
              title="Vue Kanban"
              className={cn(
                "rounded-md p-2 transition",
                viewMode === "kanban"
                  ? "bg-copper/15 text-copper-glow"
                  : "text-titanium hover:text-ivory"
              )}
            >
              <KanbanSquare className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => onViewModeChange("timeline")}
              title="Vue Timeline"
              className={cn(
                "rounded-md p-2 transition",
                viewMode === "timeline"
                  ? "bg-copper/15 text-copper-glow"
                  : "text-titanium hover:text-ivory"
              )}
            >
              <GanttChart className="h-4 w-4" />
            </button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={onExportCsv}
            className="border-copper/20"
          >
            <Download className="mr-2 h-4 w-4" />
            Exporter CSV
          </Button>

          <Button
            onClick={onAddItem}
            className="bg-copper hover:bg-copper-glow"
          >
            <Plus className="mr-2 h-4 w-4" />
            Ajouter un item
          </Button>
        </div>
      </div>

      <div className="rounded-2xl border border-copper/10 bg-obsidian/50 p-4 ring-1 ring-copper/10">
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="mr-1 text-[10px] uppercase tracking-wider text-titanium/60">
              Projets
            </span>
            {projects.map((p) => {
              const accent = getProjectAccent(p.branch);
              const active = projectFilter.includes(p.id);
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => toggleProject(p.id)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px] transition",
                    active
                      ? cn(accent.border, accent.bg, accent.color)
                      : "border-copper/15 text-titanium hover:border-copper/20"
                  )}
                >
                  <span className={cn("h-1.5 w-1.5 rounded-full", accent.dot)} />
                  {p.name}
                </button>
              );
            })}
            {projectFilter.length > 0 && (
              <button
                type="button"
                onClick={() => onProjectFilterChange([])}
                className="text-[10px] text-titanium/60 underline hover:text-copper-glow"
              >
                Tout effacer
              </button>
            )}
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="mr-1 text-[10px] uppercase tracking-wider text-titanium/60">
                Priorité
              </span>
              {ROADMAP_PRIORITIES.map(({ id, label }) => (
                <FilterChip
                  key={id}
                  active={priorityFilter.includes(id)}
                  label={label}
                  onClick={() => togglePriority(id)}
                />
              ))}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-wider text-titanium/60">
                Phase
              </span>
              <Select
                value={phaseFilter}
                onValueChange={onPhaseFilterChange}
              >
                <SelectTrigger className="h-8 w-[160px] border-copper/20 bg-obsidian text-xs">
                  <SelectValue placeholder="Toutes" />
                </SelectTrigger>
                <SelectContent className="border-copper/20 bg-surface-raised">
                  <SelectItem value="all">Toutes les phases</SelectItem>
                  {phases.map((phase) => (
                    <SelectItem key={phase} value={phase}>
                      {phase}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
