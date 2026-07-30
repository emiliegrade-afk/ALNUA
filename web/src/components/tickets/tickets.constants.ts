export type TicketType = "bug" | "feature" | "improvement" | "crash";
export type TicketPriority = "critical" | "high" | "medium" | "low";
export type TicketStatus = "open" | "in_progress" | "in_review" | "done" | "wont_fix";
export type TicketSource = "qa_agent" | "sav_bot" | "reviews_bot" | "emilie";
export type StatusTab = "open" | "in_progress" | "done" | "all";

export const STATUS_TABS: { id: StatusTab; label: string; statuses?: TicketStatus[] }[] = [
  { id: "open", label: "Ouverts", statuses: ["open"] },
  { id: "in_progress", label: "En cours", statuses: ["in_progress", "in_review"] },
  { id: "done", label: "Résolus", statuses: ["done", "wont_fix"] },
  { id: "all", label: "Tous" },
];

export const TICKET_TYPES: { id: TicketType; label: string }[] = [
  { id: "bug", label: "Bug" },
  { id: "feature", label: "Feature" },
  { id: "improvement", label: "Improvement" },
  { id: "crash", label: "Crash" },
];

export const TICKET_PRIORITIES: { id: TicketPriority; label: string }[] = [
  { id: "critical", label: "Critical" },
  { id: "high", label: "High" },
  { id: "medium", label: "Medium" },
  { id: "low", label: "Low" },
];

export const TICKET_STATUSES: { id: TicketStatus; label: string }[] = [
  { id: "open", label: "Ouvert" },
  { id: "in_progress", label: "En cours" },
  { id: "in_review", label: "En revue" },
  { id: "done", label: "Résolu" },
  { id: "wont_fix", label: "Won't fix" },
];

export const SOURCE_LABELS: Record<TicketSource, string> = {
  qa_agent: "QA Agent",
  sav_bot: "SAV Bot",
  reviews_bot: "Reviews Bot",
  emilie: "Emilie",
};

export const PRIORITY_STYLES: Record<
  TicketPriority,
  { bar: string; badge: string; label: string }
> = {
  critical: {
    bar: "bg-red-500",
    badge: "bg-red-500/20 text-red-400 border-red-500/30",
    label: "Critical",
  },
  high: {
    bar: "bg-orange-500",
    badge: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    label: "High",
  },
  medium: {
    bar: "bg-yellow-500",
    badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    label: "Medium",
  },
  low: {
    bar: "bg-zinc-500",
    badge: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
    label: "Low",
  },
};

export const TYPE_STYLES: Record<
  TicketType,
  { badge: string; label: string }
> = {
  bug: {
    badge: "bg-red-500/10 text-red-300 border-red-500/20",
    label: "Bug",
  },
  feature: {
    badge: "bg-blue-500/15 text-blue-300 border-blue-500/25",
    label: "Feature",
  },
  improvement: {
    badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/25",
    label: "Improvement",
  },
  crash: {
    badge: "bg-red-600/25 text-red-200 border-red-600/40",
    label: "Crash",
  },
};

export const STATUS_STYLES: Record<TicketStatus, string> = {
  open: "bg-copper/15 text-copper-glow border-copper/30",
  in_progress: "bg-blue-500/15 text-blue-300 border-blue-500/25",
  in_review: "bg-glow/15 text-glow border-glow/30",
  done: "bg-emerald-500/15 text-emerald-300 border-emerald-500/25",
  wont_fix: "bg-zinc-500/15 text-zinc-400 border-zinc-500/25",
};
