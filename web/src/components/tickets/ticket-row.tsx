"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { CheckCircle2, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  PRIORITY_STYLES,
  SOURCE_LABELS,
  STATUS_STYLES,
  TICKET_STATUSES,
  TYPE_STYLES,
  type TicketPriority,
  type TicketSource,
  type TicketStatus,
  type TicketType,
} from "@/components/tickets/tickets.constants";
import { getProjectAccent } from "@/lib/projects";
import type { TicketWithProject } from "@/lib/tickets";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface TicketRowProps {
  ticket: TicketWithProject;
  project?: Project;
  active?: boolean;
  onClick: () => void;
  onPromptClick: (e: React.MouseEvent) => void;
  onResolveClick: (e: React.MouseEvent) => void;
}

export function TicketRow({
  ticket,
  project,
  active,
  onClick,
  onPromptClick,
  onResolveClick,
}: TicketRowProps) {
  const priority = ticket.priority as TicketPriority;
  const type = ticket.type as TicketType;
  const status = ticket.status as TicketStatus;
  const source = ticket.source as TicketSource;

  const priorityStyle = PRIORITY_STYLES[priority] ?? PRIORITY_STYLES.medium;
  const typeStyle = TYPE_STYLES[type] ?? TYPE_STYLES.bug;
  const accent = project ? getProjectAccent(project.branch) : null;
  const statusLabel =
    TICKET_STATUSES.find((s) => s.id === status)?.label ?? status;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "group relative flex w-full items-stretch gap-0 overflow-hidden rounded-xl border text-left transition",
        active
          ? "border-copper/35 bg-copper/10 ring-1 ring-copper/20"
          : "border-copper/10 bg-surface/60 hover:border-copper/15 hover:bg-obsidian-deep/40"
      )}
    >
      <div className={cn("w-1 shrink-0", priorityStyle.bar)} />

      <div className="min-w-0 flex-1 px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant="outline"
            className={cn("border text-[10px]", typeStyle.badge)}
          >
            {typeStyle.label}
          </Badge>
          {project && (
            <Badge
              variant="outline"
              className={cn(
                "border text-[10px]",
                accent?.bg,
                accent?.color,
                accent?.border
              )}
            >
              {project.name}
            </Badge>
          )}
          <Badge
            variant="outline"
            className={cn("border text-[10px]", STATUS_STYLES[status])}
          >
            {statusLabel}
          </Badge>
        </div>

        <p className="mt-2 line-clamp-1 text-sm font-medium text-ivory">
          {ticket.title}
        </p>

        <div className="mt-1.5 flex flex-wrap items-center justify-between gap-2">
          <span className="text-[11px] text-titanium/70">
            {SOURCE_LABELS[source] ?? ticket.source}
          </span>
          <span className="text-[11px] text-titanium/50">
            {format(new Date(ticket.created_at), "d MMM yyyy", { locale: fr })}
          </span>
        </div>
      </div>

      <div className="flex shrink-0 flex-col items-center justify-center gap-1.5 pr-3">
        {status !== "done" && status !== "wont_fix" && (
          <span
            role="button"
            tabIndex={0}
            title="Marquer comme résolu"
            onClick={onResolveClick}
            onKeyDown={(e) => {
              if (e.key === "Enter") onResolveClick(e as unknown as React.MouseEvent);
            }}
            className="flex items-center gap-1 rounded-md border border-emerald-500/25 bg-emerald-500/10 px-2 py-1 text-[10px] text-emerald-400 opacity-0 transition group-hover:opacity-100 hover:bg-emerald-500/20"
          >
            <CheckCircle2 className="h-3 w-3" />
            Résolu
          </span>
        )}
        {ticket.cursor_prompt && (
          <span
            role="button"
            tabIndex={0}
            onClick={onPromptClick}
            onKeyDown={(e) => {
              if (e.key === "Enter") onPromptClick(e as unknown as React.MouseEvent);
            }}
            className="flex items-center gap-1 rounded-md border border-emerald-500/25 bg-emerald-500/10 px-2 py-1 text-[10px] text-emerald-400 opacity-0 transition group-hover:opacity-100 hover:bg-emerald-500/20"
          >
            <Zap className="h-3 w-3" />
            Prompt Cursor
          </span>
        )}
      </div>
    </button>
  );
}
