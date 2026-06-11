"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { Calendar, Link2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  getDueDateStyle,
  normalizePriority,
  PRIORITY_STYLES,
} from "@/components/roadmap/roadmap.constants";
import { getProjectAccent } from "@/lib/projects";
import type { RoadmapItem } from "@/lib/types";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface RoadmapCardProps {
  item: RoadmapItem;
  project?: Project;
  onClick: () => void;
  isDragging?: boolean;
}

export function RoadmapCard({
  item,
  project,
  onClick,
  isDragging,
}: RoadmapCardProps) {
  const accent = project ? getProjectAccent(project.branch) : null;
  const priorityStyle = PRIORITY_STYLES[normalizePriority(item.priority)];

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
      className={cn(
        "w-full cursor-pointer rounded-xl border border-white/[0.08] bg-obsidian/80 p-3 text-left shadow-sm transition",
        "hover:border-copper/25 hover:bg-obsidian",
        isDragging && "rotate-1 border-copper/40 shadow-lg ring-1 ring-copper/30"
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold leading-snug text-ivory">
          {item.title}
        </p>
        {item.linked_ticket_id && (
          <Link2 className="h-3.5 w-3.5 shrink-0 text-copper/70" aria-label="Lié à un ticket" />
        )}
      </div>

      <div className="mt-2 flex flex-wrap gap-1.5">
        {project && accent && (
          <Badge
            variant="outline"
            className={cn("text-[10px]", accent.bg, accent.border, accent.color)}
          >
            {project.name}
          </Badge>
        )}
        <Badge
          variant="outline"
          className={cn("text-[10px]", priorityStyle.badge)}
        >
          {priorityStyle.label}
        </Badge>
        {item.phase && (
          <Badge
            variant="outline"
            className="border-white/10 text-[10px] text-titanium"
          >
            {item.phase}
          </Badge>
        )}
      </div>

      {item.due_date && (
        <p
          className={cn(
            "mt-2 flex items-center gap-1 text-[11px]",
            getDueDateStyle(item.due_date)
          )}
        >
          <Calendar className="h-3 w-3" />
          {format(new Date(item.due_date), "d MMM yyyy", { locale: fr })}
        </p>
      )}
    </div>
  );
}
