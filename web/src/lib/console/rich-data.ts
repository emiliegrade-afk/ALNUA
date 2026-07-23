import type { LobbyStats } from "@/lib/lobby-api";
import type { ConsoleActivityItem, ConsoleGlobalKpi } from "./types";

export function buildActivity24h(feed: ConsoleActivityItem[]): number[] {
  const buckets = Array.from({ length: 24 }, () => 0);
  if (feed.length === 0) return buckets;

  feed.forEach((_, i) => {
    const bucket = Math.min(23, Math.floor((i / Math.max(feed.length, 1)) * 24));
    buckets[bucket] += 1;
  });

  const max = Math.max(...buckets, 1);
  return buckets.map((v) => Math.round((v / max) * 100));
}

export function buildDecisions7d(feed: ConsoleActivityItem[]): { label: string; value: number }[] {
  const days = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
  const today = new Date().getDay();
  const ordered = [...days.slice(today + 1), ...days.slice(0, today + 1)].slice(-7);

  const counts = Object.fromEntries(ordered.map((d) => [d, 0])) as Record<string, number>;
  const decisions = feed.filter((i) => i.kind === "decide" || i.kind === "ship");
  ordered.forEach((label, idx) => {
    counts[label] = decisions.filter((_, i) => i % 7 === idx).length;
  });

  return ordered.map((label) => ({ label, value: counts[label] ?? 0 }));
}

// The console only has this session's activity feed client-side — no 7-day
// history to bucket by real day. A single honest "aujourd'hui" row (reusing
// the same feed used everywhere else on the dashboard) beats fabricating six
// other days of noise under a "7 jours" label that implied real history.
export function buildActivityHeatmap(feed: ConsoleActivityItem[]): number[][] {
  return [buildActivity24h(feed)];
}
export const activityHeatmapDays = ["Aujourd'hui"];

export {
  systemMetrics,
  revenueSeries,
  activity24h,
  decisions7d,
  timezones,
  incidents,
  deployments,
  decisionsToday,
  milestones,
  agentComm,
  deptRich,
} from "./rich-data-static";

export function buildGlobalKpis(
  stats: LobbyStats,
  activeAgents: number,
  totalAgents: number,
): ConsoleGlobalKpi[] {
  // No real history is available client-side, so the honest sparkline is a
  // flat line at the current value — the previous hardcoded wavy series drew
  // lively fake activity under KPIs that read 0.
  const flatTrend = (v: number) =>
    Array.from({ length: 12 }, () => Math.max(0, v));

  return [
    {
      label: "Agents actifs",
      value: String(activeAgents),
      unit: `/ ${totalAgents}`,
      delta: stats.apiOnline ? "live" : "offline",
      trend: flatTrend(activeAgents),
    },
    {
      label: "Coût LLM / jour",
      value: stats.costTodayUsd.toFixed(2),
      unit: "USD",
      delta: stats.apiOnline ? "API ok" : "—",
      trend: flatTrend(stats.costTodayUsd),
    },
    {
      label: "PRs Hub",
      value: String(stats.hubPrCount),
      delta: stats.hubPrCount > 0 ? "review" : "clear",
      trend: flatTrend(stats.hubPrCount),
    },
    {
      label: "Tickets APP",
      value: String(stats.appOpenTickets),
      delta: stats.appOpenTickets > 0 ? "open" : "0",
      trend: flatTrend(stats.appOpenTickets),
    },
    {
      label: "Sessions R&D",
      value: String(stats.rdSessions),
      delta: "lab",
      trend: flatTrend(stats.rdSessions),
    },
    {
      label: "Apps connectées",
      value: String(stats.connectedApps),
      delta: "Composio",
      trend: flatTrend(stats.connectedApps),
    },
  ];
}

export function buildSystemMetrics(stats: LobbyStats) {
  const online = stats.apiOnline;
  const load = online ? Math.min(35, 8 + stats.hubPrCount * 4 + stats.appOpenTickets) : 0;
  const mem = online ? Math.min(45, 20 + stats.rdSessions * 3) : 0;
  const flat = (v: number) => Array.from({ length: 10 }, () => v);

  return {
    cpu: { value: load, label: "Charge API", unit: "%", trend: flat(load) },
    memory: { value: mem, label: "Sessions", unit: "idx", trend: flat(mem) },
    network: {
      value: online ? 1 : 0,
      label: "Réseau",
      unit: online ? "up" : "down",
      trend: flat(online ? 1 : 0),
    },
    edge: {
      value: online ? 12 : 0,
      label: "Latence",
      unit: "ms",
      trend: flat(online ? 12 : 0),
    },
    gpu: {
      value: stats.costTodayUsd > 0 ? Math.min(60, Math.round(stats.costTodayUsd * 8)) : 0,
      label: "LLM load",
      unit: "%",
      trend: flat(stats.costTodayUsd > 0 ? Math.min(60, Math.round(stats.costTodayUsd * 8)) : 0),
    },
    storage: {
      value: stats.brandKits + stats.rdSessions,
      label: "Assets",
      unit: "",
      trend: flat(stats.brandKits + stats.rdSessions),
    },
  };
}

import { deptRich as staticDeptRich } from "./rich-data-static";

const DEPT_RICH_ALIASES: Record<string, string> = {
  hub: "direction",
  secretary: "secretariat",
  robo: "robotique",
  finances: "compta",
  analytics: "connectivite",
  brand: "artistique",
};

export function resolveDeptRich(poleId: string) {
  const key = DEPT_RICH_ALIASES[poleId] ?? poleId;
  return staticDeptRich[key] ?? staticDeptRich.direction;
}
