import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";
import { parseHubApiError } from "./hub-api-error";

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
}

export const EMPTY_AGENTS_STATUS: AgentsStatusResponse = {
  agents: {},
  recentLogs: [],
  pipelineActive: false,
};

export type AgentsStatusResult =
  | { ok: true; data: AgentsStatusResponse }
  | { ok: false; error: string; data: AgentsStatusResponse };

export async function fetchAgentsStatus(): Promise<AgentsStatusResult> {
  try {
    const res = await fetch(hubApiUrl("/agents/status"), {
      cache: "no-store",
      headers: hubApiKeyHeaders(),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      return {
        ok: false,
        error: parseHubApiError(text, res.status),
        data: EMPTY_AGENTS_STATUS,
      };
    }
    const data = (await res.json()) as AgentsStatusResponse;
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

export function countActiveAgents(
  agents: Record<string, AgentStatus>,
): number {
  return Object.values(agents).filter(
    (s) => s.status === "working" || s.status === "waiting",
  ).length;
}
