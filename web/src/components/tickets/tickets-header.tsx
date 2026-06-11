"use client";

import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  STATUS_TABS,
  TICKET_PRIORITIES,
  TICKET_TYPES,
  type StatusTab,
  type TicketPriority,
  type TicketType,
} from "@/components/tickets/tickets.constants";
import { getProjectAccent } from "@/lib/projects";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface TicketsHeaderProps {
  projects: Project[];
  projectFilter: string;
  onProjectFilterChange: (value: string) => void;
  statusTab: StatusTab;
  onStatusTabChange: (tab: StatusTab) => void;
  priorityFilter: TicketPriority[];
  onPriorityFilterChange: (priorities: TicketPriority[]) => void;
  typeFilter: TicketType[];
  onTypeFilterChange: (types: TicketType[]) => void;
  openCount: number;
  onNewTicket: () => void;
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
          : "border-white/[0.08] text-titanium hover:border-copper/20"
      )}
    >
      {label}
    </button>
  );
}

export function TicketsHeader({
  projects,
  projectFilter,
  onProjectFilterChange,
  statusTab,
  onStatusTabChange,
  priorityFilter,
  onPriorityFilterChange,
  typeFilter,
  onTypeFilterChange,
  openCount,
  onNewTicket,
}: TicketsHeaderProps) {
  function togglePriority(id: TicketPriority) {
    onPriorityFilterChange(
      priorityFilter.includes(id)
        ? priorityFilter.filter((p) => p !== id)
        : [...priorityFilter, id]
    );
  }

  function toggleType(id: TicketType) {
    onTypeFilterChange(
      typeFilter.includes(id)
        ? typeFilter.filter((t) => t !== id)
        : [...typeFilter, id]
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="forge-heading text-[11px] text-copper/80">Support</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-wide text-ivory">
            Tickets
          </h1>
          <p className="mt-1 text-sm text-titanium">
            {openCount} ticket{openCount > 1 ? "s" : ""} ouvert
            {openCount > 1 ? "s" : ""}
          </p>
        </div>
        <Button
          onClick={onNewTicket}
          className="shrink-0 bg-copper hover:bg-copper-glow"
        >
          <Plus className="mr-2 h-4 w-4" />
          Nouveau ticket
        </Button>
      </div>

      <div className="rounded-2xl border border-copper/10 bg-obsidian/50 p-4 ring-1 ring-white/[0.04]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
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
                      <span
                        className={cn("h-1.5 w-1.5 rounded-full", accent.dot)}
                      />
                      {p.name}
                    </span>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>

          <div className="flex flex-wrap gap-1.5">
            {STATUS_TABS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => onStatusTabChange(id)}
                className={cn(
                  "rounded-lg border px-3 py-1.5 text-xs transition",
                  statusTab === id
                    ? "border-copper/45 bg-copper/10 text-copper-glow"
                    : "border-transparent text-titanium hover:border-copper/20 hover:bg-white/[0.03]"
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-[10px] uppercase tracking-wider text-titanium/60">
              Priorité
            </span>
            {TICKET_PRIORITIES.map(({ id, label }) => (
              <FilterChip
                key={id}
                active={priorityFilter.includes(id)}
                label={label}
                onClick={() => togglePriority(id)}
              />
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-[10px] uppercase tracking-wider text-titanium/60">
              Type
            </span>
            {TICKET_TYPES.map(({ id, label }) => (
              <FilterChip
                key={id}
                active={typeFilter.includes(id)}
                label={label}
                onClick={() => toggleType(id)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
