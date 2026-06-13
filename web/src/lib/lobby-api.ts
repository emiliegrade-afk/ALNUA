import { fetchTodayBriefing } from "@/lib/briefing-api";
import { fetchComposioApps } from "@/lib/composio-api";
import { fetchProjects, fetchTickets } from "@/lib/api";
import { fetchBrandKits } from "@/lib/brand-api";
import { fetchPosts } from "@/lib/content";
import { checkApiHealth } from "@/lib/hub-health";
import { hubFetch } from "@/lib/hub-fetch";

import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";

async function apiGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(hubApiUrl(path), {
      cache: "no-store",
      headers: hubApiKeyHeaders(),
    });
    if (!res.ok) return null;
    return res.json() as Promise<T>;
  } catch {
    return null;
  }
}

export interface LobbyStats {
  apiOnline: boolean;
  apiAuthenticated: boolean;
  ceoNotifications: number;
  hubPrCount: number;
  appOpenTickets: number;
  gamingStatus: string;
  roboStatus: string;
  financesMonthTotal: string;
  marketingPendingPosts: number;
  rdSessions: number;
  brandKits: number;
  connectedApps: number;
}

const LOBBY_STATS_CACHE_TTL_MS = 60_000;

let lobbyStatsCache: LobbyStats | null = null;
let lobbyStatsCacheAt = 0;
let lobbyStatsInflight: Promise<LobbyStats> | null = null;

async function fetchLobbyStatsUncached(): Promise<LobbyStats> {
  const [
    apiHealth,
    briefing,
    projects,
    prs,
    monthCosts,
    pendingPostsRaw,
    kits,
    apps,
    sessions,
  ] = await Promise.all([
    checkApiHealth(),
    fetchTodayBriefing().catch(() => null),
    fetchProjects().catch(() => []),
    apiGet<unknown[]>("/github/prs"),
    apiGet<{ total_usd?: number }>("/costs/month"),
    fetchPosts({ status: "pending" }).catch(() => []),
    fetchBrandKits().catch(() => []),
    fetchComposioApps().catch(() => []),
    apiGet<unknown[]>("/brainstorm/sessions"),
  ]);

  let appOpenTickets = 0;
  const appProjects = projects.filter((p) => p.branch === "app");
  if (appProjects.length > 0) {
    const ticketCounts = await Promise.all(
      appProjects.map((p) =>
        fetchTickets(p.id, "open").catch(() => [])
      )
    );
    appOpenTickets = ticketCounts.reduce((sum, t) => sum + t.length, 0);
  }

  const gamingProjects = projects.filter((p) => p.branch === "gaming");
  const roboProjects = projects.filter((p) => p.branch === "robotics");

  const ceoNotifications = briefing
    ? briefing.has_urgent
      ? briefing.urgent_count
      : briefing.pending_count
    : 0;

  return {
    apiOnline: apiHealth.online,
    apiAuthenticated: apiHealth.authenticated,
    ceoNotifications,
    hubPrCount: prs?.length ?? 0,
    appOpenTickets,
    gamingStatus:
      gamingProjects.length > 0
        ? `${gamingProjects[0]?.name ?? "Wyrdheim"} R&D en cours`
        : "Wyrdheim R&D en cours",
    roboStatus:
      roboProjects.find((p) => p.name.toLowerCase().includes("eve"))
        ? "Eve — Prototype"
        : "Eve — Prototype",
    financesMonthTotal: `$${(monthCosts?.total_usd ?? 0).toFixed(2)}`,
    marketingPendingPosts: pendingPostsRaw?.length ?? 0,
    rdSessions: sessions?.length ?? 0,
    brandKits: Array.isArray(kits) ? kits.length : 0,
    connectedApps: apps.length,
  };
}

/** Lobby aggregates — cached 60s client-side to avoid refetch on every visit. */
export async function fetchLobbyStats(options?: {
  force?: boolean;
}): Promise<LobbyStats> {
  const now = Date.now();
  if (
    !options?.force &&
    lobbyStatsCache &&
    now - lobbyStatsCacheAt < LOBBY_STATS_CACHE_TTL_MS
  ) {
    return lobbyStatsCache;
  }

  if (!options?.force && lobbyStatsInflight) {
    return lobbyStatsInflight;
  }

  lobbyStatsInflight = fetchLobbyStatsUncached()
    .then((stats) => {
      lobbyStatsCache = stats;
      lobbyStatsCacheAt = Date.now();
      return stats;
    })
    .finally(() => {
      lobbyStatsInflight = null;
    });

  return lobbyStatsInflight;
}

export async function fetchBriefToday(): Promise<{
  date?: string;
  summary?: string;
  urgent?: string[];
}> {
  return (await apiGet("/brief/today")) ?? {};
}

export type PipelineIssue = {
  number: number;
  title: string;
  labels?: string[];
  _repo_slug?: string;
  _repo_name?: string;
  _github_repo?: string;
};

export type GithubPr = {
  number: number;
  title: string;
  url?: string;
  html_url?: string;
  repo_slug?: string;
  repo_name?: string;
};

export async function fetchGithubPrs(): Promise<GithubPr[]> {
  return (await apiGet("/github/prs")) ?? [];
}

export async function fetchPipelineIssues(): Promise<PipelineIssue[]> {
  return (await apiGet("/pipeline/issues")) ?? [];
}

export type PipelineRunResponse = {
  status: string;
  task_id: string;
  issue: number;
  repo?: string | null;
};

export type PipelineStatus = {
  status: string;
  log: string[];
  progress: number;
};

export async function runPipelineIssue(
  issueNumber: number,
  repoSlug?: string,
): Promise<PipelineRunResponse> {
  const query = repoSlug ? `?repo=${encodeURIComponent(repoSlug)}` : "";
  const res = await fetch(hubApiUrl(`/pipeline/run/${issueNumber}${query}`), {
    method: "POST",
    headers: hubApiKeyHeaders(),
  });
  if (!res.ok) {
    throw new Error(`Pipeline start failed: ${res.status}`);
  }
  return res.json() as Promise<PipelineRunResponse>;
}

export async function fetchPipelineStatus(
  taskId: string,
): Promise<PipelineStatus | null> {
  return apiGet(`/pipeline/status/${taskId}`);
}

export async function fetchWeeklyCosts(): Promise<{
  total_usd?: number;
  by_day?: Array<Record<string, string | number>>;
}> {
  return (await apiGet("/costs/week")) ?? {};
}

export async function fetchEveStatus(): Promise<{
  connected: boolean;
  battery?: number | null;
}> {
  return (await apiGet("/eve/status")) ?? { connected: false };
}

export async function fetchBomEve(): Promise<
  Array<{
    id: string;
    name: string;
    category: string;
    quantity: number;
    unit_cost: number | null;
    status: string;
  }>
> {
  try {
    const data = await hubFetch<{ items: Array<Record<string, unknown>> }>("/bom/eve");
    return (data.items ?? []).map((row) => ({
      id: String(row.id),
      name: String(row.component ?? row.name ?? "—"),
      category: String(row.category ?? "autre"),
      quantity: Number(row.quantity ?? 1),
      unit_cost:
        row.unit_price != null
          ? Number(row.unit_price)
          : row.unit_cost != null
            ? Number(row.unit_cost)
            : null,
      status: String(row.status ?? "a_commander"),
    }));
  } catch {
    return [];
  }
}

export async function checkNwiroHost(): Promise<boolean> {
  const host = process.env.NEXT_PUBLIC_NWIRO_HOST?.replace(/\/$/, "");
  if (!host) return false;
  try {
    const res = await fetch(`${host}/health`, {
      method: "GET",
      signal: AbortSignal.timeout(5000),
    });
    return res.ok;
  } catch {
    try {
      const res = await fetch(host, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });
      return res.ok;
    } catch {
      return false;
    }
  }
}
