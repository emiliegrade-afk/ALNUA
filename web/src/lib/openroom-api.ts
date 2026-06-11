const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export type AgentStatusKind = "idle" | "working" | "waiting" | "error";

export interface AgentStatus {
  status: AgentStatusKind;
  currentTask?: string;
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

export async function fetchAgentsStatus(): Promise<AgentsStatusResponse> {
  try {
    const res = await fetch(`${API_URL}/agents/status`, { cache: "no-store" });
    if (!res.ok) {
      return { agents: {}, recentLogs: [], pipelineActive: false };
    }
    return res.json() as Promise<AgentsStatusResponse>;
  } catch {
    return { agents: {}, recentLogs: [], pipelineActive: false };
  }
}

export function countActiveAgents(
  agents: Record<string, AgentStatus>,
): number {
  return Object.values(agents).filter(
    (s) => s.status === "working" || s.status === "waiting",
  ).length;
}
