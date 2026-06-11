"use client";

import { useMemo, useRef } from "react";
import {
  addDays,
  addMonths,
  differenceInDays,
  endOfMonth,
  format,
  startOfMonth,
} from "date-fns";
import { fr } from "date-fns/locale";
import {
  normalizePriority,
  normalizeStatus,
  PRIORITY_STYLES,
  ROADMAP_STATUSES,
} from "@/components/roadmap/roadmap.constants";
import { getProjectAccent } from "@/lib/projects";
import type { RoadmapItem } from "@/lib/types";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

const DAY_WIDTH = 4;
const ROW_HEIGHT = 44;
const LABEL_WIDTH = 140;

interface RoadmapTimelineProps {
  items: RoadmapItem[];
  projects: Project[];
  onItemClick: (id: string) => void;
}

function getBarRange(item: RoadmapItem): { start: Date; end: Date } {
  const start = new Date(item.created_at);
  start.setHours(0, 0, 0, 0);
  if (item.due_date) {
    const end = new Date(item.due_date);
    end.setHours(0, 0, 0, 0);
    if (end < start) return { start: end, end: start };
    return { start, end };
  }
  return { start, end: addDays(start, 14) };
}

export function RoadmapTimeline({
  items,
  projects,
  onItemClick,
}: RoadmapTimelineProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const { rangeStart, totalDays, months } = useMemo(() => {
    const now = new Date();
    const start = startOfMonth(addMonths(now, -1));
    const end = endOfMonth(addMonths(now, 1));
    const days = differenceInDays(end, start) + 1;
    const monthList: { label: string; offset: number; width: number }[] = [];
    let cursor = start;
    while (cursor <= end) {
      const mStart = startOfMonth(cursor);
      const mEnd = endOfMonth(cursor);
      const clipStart = mStart < start ? start : mStart;
      const clipEnd = mEnd > end ? end : mEnd;
      const offset = differenceInDays(clipStart, start);
      const width = differenceInDays(clipEnd, clipStart) + 1;
      monthList.push({
        label: format(cursor, "MMMM yyyy", { locale: fr }),
        offset,
        width,
      });
      cursor = addMonths(startOfMonth(cursor), 1);
    }
    return {
      rangeStart: start,
      totalDays: days,
      months: monthList,
    };
  }, []);

  const projectRows = useMemo(() => {
    const ids = new Set(items.map((i) => i.project_id));
    return projects.filter((p) => ids.has(p.id));
  }, [items, projects]);

  const timelineWidth = totalDays * DAY_WIDTH;

  function dayOffset(date: Date): number {
    return differenceInDays(date, rangeStart) * DAY_WIDTH;
  }

  return (
    <div className="rounded-2xl border border-copper/10 bg-obsidian/40 ring-1 ring-white/[0.04]">
      <div
        ref={scrollRef}
        className="overflow-x-auto"
        style={{ maxHeight: "calc(100dvh - 22rem)" }}
      >
        <div style={{ minWidth: LABEL_WIDTH + timelineWidth + 32 }}>
          {/* Month headers */}
          <div className="flex border-b border-white/[0.06]">
            <div
              className="shrink-0 border-r border-white/[0.06] bg-obsidian/60"
              style={{ width: LABEL_WIDTH }}
            />
            <div className="relative" style={{ width: timelineWidth, height: 36 }}>
              {months.map((m) => (
                <div
                  key={m.label}
                  className="absolute top-0 flex h-full items-center border-r border-white/[0.06] px-2 text-xs capitalize text-titanium"
                  style={{ left: m.offset * DAY_WIDTH, width: m.width * DAY_WIDTH }}
                >
                  {m.label}
                </div>
              ))}
            </div>
          </div>

          {/* Project rows */}
          {projectRows.length === 0 ? (
            <p className="p-8 text-center text-sm text-titanium">
              Aucun item à afficher sur la timeline
            </p>
          ) : (
            projectRows.map((project) => {
              const accent = getProjectAccent(project.branch);
              const rowItems = items.filter((i) => i.project_id === project.id);
              return (
                <div
                  key={project.id}
                  className="flex border-b border-white/[0.04]"
                  style={{ height: ROW_HEIGHT }}
                >
                  <div
                    className="flex shrink-0 items-center gap-2 border-r border-white/[0.06] bg-obsidian/60 px-3"
                    style={{ width: LABEL_WIDTH }}
                  >
                    <span className={cn("h-2 w-2 rounded-full", accent.dot)} />
                    <span className="truncate text-xs font-medium text-ivory">
                      {project.name}
                    </span>
                  </div>
                  <div
                    className="relative"
                    style={{ width: timelineWidth, height: ROW_HEIGHT }}
                  >
                    {/* Today marker */}
                    <div
                      className="absolute top-0 z-10 h-full w-px bg-copper/50"
                      style={{ left: dayOffset(new Date()) }}
                    />
                    {rowItems.map((item) => {
                      const { start, end } = getBarRange(item);
                      const left = Math.max(0, dayOffset(start));
                      const right = dayOffset(end) + DAY_WIDTH;
                      const width = Math.max(DAY_WIDTH * 7, right - left);
                      const statusLabel = ROADMAP_STATUSES.find(
                        (s) => s.id === normalizeStatus(item.status)
                      )?.label;
                      const priorityLabel =
                        PRIORITY_STYLES[normalizePriority(item.priority)].label;
                      return (
                        <button
                          key={item.id}
                          type="button"
                          title={`${item.title} · ${statusLabel} · ${priorityLabel}`}
                          onClick={() => onItemClick(item.id)}
                          className={cn(
                            "absolute top-2 z-20 h-7 truncate rounded-md border px-2 text-left text-[10px] font-medium shadow-sm transition hover:brightness-110",
                            accent.bg,
                            accent.border,
                            accent.color
                          )}
                          style={{
                            left,
                            width,
                            maxWidth: timelineWidth - left,
                          }}
                        >
                          {item.title}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
