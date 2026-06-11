import type { RoadmapPriority, RoadmapStatus } from "@/lib/types";

export type RoadmapViewMode = "kanban" | "timeline";

export const ROADMAP_STATUSES: {
  id: RoadmapStatus;
  label: string;
  emoji: string;
}[] = [
  { id: "idea", label: "Idée", emoji: "💡" },
  { id: "planned", label: "Planifié", emoji: "📋" },
  { id: "in_progress", label: "En cours", emoji: "⚡" },
  { id: "done", label: "Terminé", emoji: "✅" },
];

export const ROADMAP_PRIORITIES: { id: RoadmapPriority; label: string }[] = [
  { id: "critical", label: "Critical" },
  { id: "high", label: "High" },
  { id: "medium", label: "Medium" },
  { id: "low", label: "Low" },
];

export const PRIORITY_STYLES: Record<
  RoadmapPriority,
  { badge: string; bar: string; label: string }
> = {
  critical: {
    badge: "bg-red-500/20 text-red-400 border-red-500/30",
    bar: "bg-red-500",
    label: "Critical",
  },
  high: {
    badge: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    bar: "bg-orange-500",
    label: "High",
  },
  medium: {
    badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    bar: "bg-yellow-500",
    label: "Medium",
  },
  low: {
    badge: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
    bar: "bg-zinc-500",
    label: "Low",
  },
};

export const STATUS_STYLES: Record<RoadmapStatus, string> = {
  idea: "bg-violet-500/15 text-violet-300 border-violet-500/25",
  planned: "bg-copper/15 text-copper-glow border-copper/30",
  in_progress: "bg-blue-500/15 text-blue-300 border-blue-500/25",
  done: "bg-emerald-500/15 text-emerald-300 border-emerald-500/25",
};

const VALID_PRIORITIES = new Set<RoadmapPriority>([
  "critical",
  "high",
  "medium",
  "low",
]);

const VALID_STATUSES = new Set<RoadmapStatus>([
  "idea",
  "planned",
  "in_progress",
  "done",
]);

export function normalizePriority(value: unknown): RoadmapPriority {
  if (
    typeof value === "string" &&
    VALID_PRIORITIES.has(value as RoadmapPriority)
  ) {
    return value as RoadmapPriority;
  }
  const n = Number(value);
  if (!Number.isNaN(n)) {
    if (n >= 8) return "critical";
    if (n >= 6) return "high";
    if (n >= 3) return "medium";
    return "low";
  }
  return "medium";
}

export function normalizeStatus(value: unknown): RoadmapStatus {
  if (
    typeof value === "string" &&
    VALID_STATUSES.has(value as RoadmapStatus)
  ) {
    return value as RoadmapStatus;
  }
  return "planned";
}

export function getDueDateStyle(dueDate: string | null): string {
  if (!dueDate) return "text-titanium/70";
  const due = new Date(dueDate);
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  due.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil(
    (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  );
  if (diffDays < 0) return "text-red-400";
  if (diffDays <= 7) return "text-orange-400";
  return "text-titanium/70";
}
