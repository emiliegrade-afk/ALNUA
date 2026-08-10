/** Mission Graph client — Phase B (DEC-023). */

import { hubFetch } from "./hub-fetch";

export type MissionStatus =
  | "DRAFTED"
  | "IN_PROGRESS"
  | "BLOCKED"
  | "COMPLETED"
  | "FAILED"
  | "A_VERIFIER";

export interface MissionSummary {
  mission_id: string;
  title: string;
  status: MissionStatus;
  objective: string;
  progress_pct: number;
  task_count: number;
  created_at: string;
  updated_at: string;
  finished_at?: string | null;
  source: string;
}

export interface MissionGraphNode {
  id: string;
  agent_id: string;
  status: string;
  label: string;
}

export interface MissionDetail extends MissionSummary {
  context?: string;
  tasks: Array<Record<string, unknown>>;
  graph: {
    nodes: MissionGraphNode[];
    edges: Array<{ from: string; to: string }>;
    by_status: Record<string, number>;
    progress_pct: number;
  };
}

export async function listMissions(limit = 30): Promise<MissionSummary[]> {
  const data = await hubFetch<{ missions: MissionSummary[] }>(
    `/missions?limit=${limit}`,
  );
  return data.missions ?? [];
}

export async function getMission(missionId: string): Promise<MissionDetail> {
  return hubFetch<MissionDetail>(`/missions/${encodeURIComponent(missionId)}`);
}

export async function createMissionFromPlan(body: {
  title: string;
  objective?: string;
  steps: Array<{
    task_id: string;
    description?: string;
    agent_id: string;
    method: string;
    kwargs?: Record<string, unknown>;
    depends_on?: string[];
  }>;
  run?: boolean;
}): Promise<{ mission: MissionDetail; run?: Record<string, unknown> }> {
  return hubFetch("/missions/from-plan", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function runMission(
  missionId: string,
  opts?: { max_concurrent?: number; stop_on_failure?: boolean },
): Promise<Record<string, unknown>> {
  return hubFetch(`/missions/${encodeURIComponent(missionId)}/run`, {
    method: "POST",
    body: JSON.stringify(opts ?? {}),
  });
}
