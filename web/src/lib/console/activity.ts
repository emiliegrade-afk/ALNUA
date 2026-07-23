import type { OpenRoomLogEntry } from "@/lib/openroom-api";
import type { ActivityKind, ConsoleActivityItem } from "./types";

function inferKind(message: string): ActivityKind {
  const m = message.toLowerCase();
  if (/ship|deploy|merge|release|livré|merged|pr/.test(m)) return "ship";
  if (/decid|valid|approuv|brief|plan/.test(m)) return "decide";
  if (/research|r&d|veille|hypoth|brainstorm/.test(m)) return "research";
  if (/error|fail|alert|bug|incident/.test(m)) return "alert";
  return "create";
}

function formatLogTime(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

export function buildActivityFeed(logs: OpenRoomLogEntry[]): ConsoleActivityItem[] {
  return logs.map((log, i) => ({
    id: `log-${i}-${log.time}`,
    kind: inferKind(log.message),
    agent: log.agent,
    dept: "Hub",
    action: log.message,
    time: formatLogTime(log.time),
  }));
}

export const FALLBACK_ACTIVITY: ConsoleActivityItem[] = [
  {
    id: "fallback-1",
    kind: "create",
    agent: "Aria Voss",
    dept: "Direction",
    action: "Console ALNUA initialisée — en attente de flux live",
    time: "—",
  },
];
