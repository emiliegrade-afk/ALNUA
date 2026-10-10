"use client";

import {
  Globe,
  Loader2,
  Mail,
  CalendarDays,
  Users,
  PenLine,
  ListTodo,
  BarChart3,
  AlignLeft,
  ExternalLink,
  Image,
} from "lucide-react";

import type { LiveTask } from "@/lib/live-api";
import { workKind, WORK_LABEL, type LiveWorkKind } from "@/lib/live-work";
import { isActive } from "@/store/live-store";
import { cn } from "@/lib/utils";

const ICONS: Record<LiveWorkKind, typeof Globe> = {
  research: Globe,
  open: ExternalLink,
  mail: Mail,
  calendar: CalendarDays,
  plan: Users,
  write: PenLine,
  chart: BarChart3,
  summary: AlignLeft,
  image: Image,
  other: ListTodo,
};

/** One tile per job in flight — several can run at once without mixing captions. */
export function LiveActivityRail({ tasks }: { tasks: LiveTask[] }) {
  const active = tasks.filter(isActive);
  if (active.length === 0) return null;

  return (
    <section aria-label="En cours" className="space-y-2">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-copper-light">
        En parallèle · {active.length}
      </h2>
      <ul className="grid gap-2 sm:grid-cols-2">
        {active.map((task) => {
          const kind = workKind(task);
          const Icon = ICONS[kind];
          return (
            <li
              key={task.id}
              className={cn(
                "flex gap-3 rounded-lg border p-3",
                kind === "research"
                  ? "border-sky-400/30 bg-sky-400/5"
                  : "border-copper/20 bg-obsidian-2",
              )}
            >
              <Icon
                className={cn(
                  "mt-0.5 size-5 shrink-0",
                  kind === "research" ? "text-sky-300" : "text-copper-light",
                )}
              />
              <div className="min-w-0">
                <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-zinc-400">
                  <Loader2 className="size-3 animate-spin" />
                  {WORK_LABEL[kind]}
                  {task.status === "queued" ? " · file" : ""}
                </p>
                <p className="mt-0.5 line-clamp-2 text-sm text-ivory">{task.instruction}</p>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
