import { fetchBriefingBadge } from "@/lib/briefing-api";

import { fetchComposioApps } from "@/lib/composio-api";

import { fetchProjects, fetchTickets } from "@/lib/api";

import { fetchBrandKits } from "@/lib/brand-api";

import { fetchPosts } from "@/lib/content";

import { resolveHubHealthFast, getLastKnownGoodHealth, type ApiHealthStatus } from "@/lib/hub-health";

import { hubFetch } from "@/lib/hub-fetch";



import { hubApiUrl } from "./hub-api-config";

import { hubApiKeyHeaders } from "./hub-api-key";



async function apiGet<T>(path: string, timeoutMs = 8_000): Promise<T | null> {

  try {

    const res = await fetch(hubApiUrl(path), {

      cache: "no-store",

      signal: AbortSignal.timeout(timeoutMs),

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
  costTodayUsd: number;
  /** Present when the last live refresh hit API/auth issues */
  refreshError?: string;
}

const DEFAULT_LOBBY_STATS: LobbyStats = {
  apiOnline: false,
  apiAuthenticated: false,
  ceoNotifications: 0,
  hubPrCount: 0,
  appOpenTickets: 0,
  gamingStatus: "Wyrdheim R&D en cours",
  roboStatus: "Eve — Prototype",
  financesMonthTotal: "$0.00",
  marketingPendingPosts: 0,
  rdSessions: 0,
  brandKits: 0,
  connectedApps: 0,
  costTodayUsd: 0,
};

/** Merge partial/stale cache payloads with safe defaults. */
export function normalizeLobbyStats(
  partial: Partial<LobbyStats> | null | undefined,
): LobbyStats {
  if (!partial) return { ...DEFAULT_LOBBY_STATS };
  return {
    ...DEFAULT_LOBBY_STATS,
    ...partial,
    costTodayUsd: Number(partial.costTodayUsd ?? 0),
    ceoNotifications: Number(partial.ceoNotifications ?? 0),
    hubPrCount: Number(partial.hubPrCount ?? 0),
    appOpenTickets: Number(partial.appOpenTickets ?? 0),
    marketingPendingPosts: Number(partial.marketingPendingPosts ?? 0),
    rdSessions: Number(partial.rdSessions ?? 0),
    brandKits: Number(partial.brandKits ?? 0),
    connectedApps: Number(partial.connectedApps ?? 0),
  };
}



const LOBBY_STATS_CACHE_TTL_MS = 120_000;

const LOBBY_STATS_STORAGE_KEY = "alnua_lobby_stats_v3";



let lobbyStatsCache: LobbyStats | null = null;

let lobbyStatsCacheAt = 0;

let lobbyStatsInflight: Promise<LobbyStats> | null = null;



function readLobbyStatsStorage(): LobbyStats | null {

  if (typeof window === "undefined") return null;

  try {

    const raw = sessionStorage.getItem(LOBBY_STATS_STORAGE_KEY);

    if (!raw) return null;

    const parsed = JSON.parse(raw) as { at: number; stats: LobbyStats };

    if (!parsed?.stats || typeof parsed.at !== "number") return null;

    if (Date.now() - parsed.at > LOBBY_STATS_CACHE_TTL_MS) return null;

    return normalizeLobbyStats(parsed.stats);

  } catch {

    return null;

  }

}



function writeLobbyStatsStorage(stats: LobbyStats): void {

  if (typeof window === "undefined") return;

  try {

    sessionStorage.setItem(

      LOBBY_STATS_STORAGE_KEY,

      JSON.stringify({ at: Date.now(), stats })

    );

  } catch {

    // ignore quota errors

  }

}



/** Synchronous cache read — use for instant lobby paint on navigation. */

export function getLobbyStatsCache(): LobbyStats | null {

  if (

    lobbyStatsCache &&

    Date.now() - lobbyStatsCacheAt < LOBBY_STATS_CACHE_TTL_MS

  ) {

    return normalizeLobbyStats(lobbyStatsCache);

  }

  const stored = readLobbyStatsStorage();

  if (stored) {

    lobbyStatsCache = normalizeLobbyStats(stored);

    lobbyStatsCacheAt = Date.now();

    return lobbyStatsCache;

  }

  return null;

}



function storeLobbyStats(stats: LobbyStats): LobbyStats {

  const normalized = normalizeLobbyStats(stats);

  lobbyStatsCache = normalized;

  lobbyStatsCacheAt = Date.now();

  writeLobbyStatsStorage(normalized);

  return normalized;

}



function ceoNotificationsFromBadge(

  badge: Awaited<ReturnType<typeof fetchBriefingBadge>>

): number {

  if (!badge) return 0;

  return badge.has_urgent ? badge.urgent_count : badge.pending_count;

}



async function fetchLobbyStatsUncached(): Promise<LobbyStats> {

  const [

    apiHealth,

    briefingBadge,

    projects,

    prs,

    monthCosts,

    pendingPostsRaw,

    kits,

    apps,

    sessions,

    costsToday,

  ] = await Promise.all([

    resolveHubHealthFast(),

    fetchBriefingBadge(),

    fetchProjects().catch(() => []),

    apiGet<unknown[]>("/github/prs", 5_000),

    apiGet<{ total_usd?: number }>("/costs/month", 5_000),

    fetchPosts({ status: "pending" }).catch(() => []),

    fetchBrandKits().catch(() => []),

    fetchComposioApps().catch(() => []),

    apiGet<unknown[]>("/brainstorm/sessions", 5_000),

    apiGet<{ total_usd?: number }>("/costs/today", 5_000),

  ]);



  let appOpenTickets = 0;

  const appProjects = projects.filter((p) => p.branch === "app");

  if (appProjects.length > 0) {

    const ticketCounts = await Promise.all(

      appProjects.map((p) => fetchTickets(p.id).catch(() => []))

    );

    appOpenTickets = ticketCounts.reduce(
      (sum, list) =>
        sum +
        list.filter(
          (t) => t.status === "open" || t.status === "in_progress"
        ).length,
      0
    );

  }



  const gamingProjects = projects.filter((p) => p.branch === "gaming");

  const roboProjects = projects.filter((p) => p.branch === "robotics");



  const previous = getLobbyStatsCache();
  const staleAuth = getLastKnownGoodHealth();
  const apiOnline =
    apiHealth.online || previous?.apiOnline || staleAuth?.online || false;
  const apiAuthenticated =
    apiHealth.authenticated ||
    previous?.apiAuthenticated ||
    staleAuth?.authenticated ||
    false;

  return {
    apiOnline,
    apiAuthenticated,
    ceoNotifications: ceoNotificationsFromBadge(briefingBadge),
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
    costTodayUsd: costsToday?.total_usd ?? 0,
    refreshError:
      !apiHealth.online && !previous?.apiOnline && !staleAuth?.online
        ? "API Hub hors ligne — stats partielles ou en cache."
        : !apiHealth.authenticated &&
            !previous?.apiAuthenticated &&
            !staleAuth?.authenticated
          ? "Clé API Hub invalide — vérifie HUB_API_KEY dans web/.env.local."
          : undefined,
  };
}



function refreshLobbyStatsInBackground(): void {

  void fetchLobbyStats({ force: true }).catch(() => {

    // keep stale cache on background failure

  });

}



/** Lobby aggregates — stale-while-revalidate, cached 2 min client-side. */

export async function fetchLobbyStats(options?: {

  force?: boolean;

}): Promise<LobbyStats> {

  const cached = getLobbyStatsCache();

  if (cached && !options?.force) {

    refreshLobbyStatsInBackground();

    return cached;

  }



  if (!options?.force && lobbyStatsInflight) {

    return lobbyStatsInflight;

  }



  lobbyStatsInflight = fetchLobbyStatsUncached()

    .then(storeLobbyStats)

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

  return (await apiGet("/github/prs", 5_000)) ?? [];

}



export async function fetchPipelineIssues(): Promise<PipelineIssue[]> {

  return (await apiGet("/pipeline/issues", 5_000)) ?? [];

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

  return apiGet(`/pipeline/status/${taskId}`, 5_000);

}



export async function fetchWeeklyCosts(): Promise<{

  total_usd?: number;

  by_day?: Array<Record<string, string | number>>;

}> {

  return (await apiGet("/costs/week", 5_000)) ?? {};

}



export async function fetchEveStatus(): Promise<{

  connected: boolean;

  battery?: number | null;

}> {

  return (await apiGet("/eve/status", 5_000)) ?? { connected: false };

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

    const data = await hubFetch<{ items: Array<Record<string, unknown>> }>(

      "/bom/eve",

      { timeoutMs: 8_000 }

    );

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



export type { ApiHealthStatus };

