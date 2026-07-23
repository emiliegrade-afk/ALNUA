import { hubFetch } from "./hub-fetch";

export type AgentStatusKind = "idle" | "working" | "waiting" | "error";

export interface AgentStatus {
  status: AgentStatusKind;
  currentTask?: string;
  currentFile?: string;
  recentCode?: string[];
  log?: string[];
  progress?: number;
}

export interface OpenRoomLogEntry {
  time: string;
  agent: string;
  message: string;
}

export interface AgentsStatusResponse {
  agents: Record<string, AgentStatus>;
  recentLogs: OpenRoomLogEntry[];
  pipelineActive: boolean;
  codingPipeline?: {
    activeTasks: number;
    githubInPipeline: number;
    githubAgentReady: number;
    githubFailed: number;
    inPipelineIssues: Array<{
      issue_number?: number;
      title?: string;
      repo_slug?: string;
    }>;
  };
}

export const EMPTY_AGENTS_STATUS: AgentsStatusResponse = {
  agents: {},
  recentLogs: [],
  pipelineActive: false,
};

export type AgentsStatusResult =
  | { ok: true; data: AgentsStatusResponse }
  | { ok: false; error: string; data: AgentsStatusResponse };

const AGENTS_STATUS_CACHE_MS = 10_000;
let agentsStatusInflight: Promise<AgentsStatusResult> | null = null;
let agentsStatusCache: { at: number; result: AgentsStatusResult } | null = null;

async function fetchAgentsStatusUncached(): Promise<AgentsStatusResult> {
  try {
    const data = await hubFetch<AgentsStatusResponse>("/agents/status", {
      timeoutMs: 25_000,
    });
    return { ok: true, data };
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Connexion agents indisponible";
    return {
      ok: false,
      error: message,
      data: EMPTY_AGENTS_STATUS,
    };
  }
}

export async function fetchAgentsStatus(): Promise<AgentsStatusResult> {
  const now = Date.now();
  if (
    agentsStatusCache &&
    now - agentsStatusCache.at < AGENTS_STATUS_CACHE_MS
  ) {
    return agentsStatusCache.result;
  }
  if (agentsStatusInflight) {
    return agentsStatusInflight;
  }
  agentsStatusInflight = fetchAgentsStatusUncached()
    .then((result) => {
      agentsStatusCache = { at: Date.now(), result };
      return result;
    })
    .finally(() => {
      agentsStatusInflight = null;
    });
  return agentsStatusInflight;
}

export function countActiveAgents(
  agents: Record<string, AgentStatus>,
): number {
  return Object.values(agents).filter(
    (s) => s.status === "working" || s.status === "waiting",
  ).length;
}
