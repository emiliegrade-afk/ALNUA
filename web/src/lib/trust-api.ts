import { hubFetch } from "./hub-fetch";

/** Agent trust row from GET /agents/trust (Phase 31 / DEC-011). */
export interface AgentTrustRow {
  agent_id: string;
  score: number;
  samples?: number;
  successes?: number;
  failures?: number;
  updated_at?: string;
  provisional?: boolean;
}

export type TrustBand = "low" | "review" | "autonomous";

/** DEC-011 bands: <70% manager, 70–90% Review Board, >90% autonome. */
export function trustBand(score: number): TrustBand {
  const pct = score * 100;
  if (pct < 70) return "low";
  if (pct <= 90) return "review";
  return "autonomous";
}

export function trustBandLabel(band: TrustBand): string {
  switch (band) {
    case "low":
      return "Validation manager";
    case "review":
      return "Review Board";
    case "autonomous":
      return "Autonomie faible risque";
  }
}

export function trustPercent(score: number): number {
  return Math.round(Math.max(0, Math.min(1, score)) * 100);
}

export async function fetchAgentTrustList(limit = 50): Promise<AgentTrustRow[]> {
  const data = await hubFetch<{ agents: AgentTrustRow[] }>(
    `/agents/trust?limit=${encodeURIComponent(String(limit))}`,
  );
  return Array.isArray(data.agents) ? data.agents : [];
}

/** Trust Graph decision row — GET /trust-graph/recent (DEC-026). */
export interface TrustGraphDecision {
  ts?: string;
  agent_id: string;
  capability: string;
  allowed: boolean;
  reason?: string;
  resource?: string | null;
}

export async function fetchTrustGraphRecent(limit = 30): Promise<TrustGraphDecision[]> {
  const data = await hubFetch<{ decisions: TrustGraphDecision[] }>(
    `/trust-graph/recent?limit=${encodeURIComponent(String(limit))}`,
  );
  return Array.isArray(data.decisions) ? data.decisions : [];
}

export type ReviewBoardCheck = {
  id: string;
  ok?: boolean;
  weight?: number;
  error?: string;
  flags?: unknown;
  reviewer?: string;
};

export type ReviewBoardResult = {
  department: string;
  gate_open: boolean;
  score: number;
  threshold: number;
  recommendation?: string;
  checks?: ReviewBoardCheck[];
  brand_review?: { ok?: boolean; flags?: unknown };
};

export async function evaluateReviewBoard(input: {
  department: string;
  title: string;
  body: string;
  status?: string;
  producer_agent_id?: string;
  record_trust?: boolean;
}): Promise<ReviewBoardResult> {
  return hubFetch<ReviewBoardResult>("/review-board/evaluate", {
    method: "POST",
    body: JSON.stringify({
      department: input.department,
      producer_agent_id: input.producer_agent_id || null,
      record_trust: input.record_trust ?? false,
      artifact: {
        title: input.title,
        body: input.body,
        status: input.status || "to_review",
      },
    }),
    timeoutMs: 20_000,
  });
}

/** Phase 36 — cross-dept work queue item. */
export type CrossDeptItem = {
  id: string;
  at?: string;
  event_type?: string;
  department: string;
  action: string;
  title?: string;
  status: string;
  result_summary?: string | null;
  artifact_path?: string | null;
};

export async function fetchCrossDeptQueue(limit = 30, status?: string): Promise<CrossDeptItem[]> {
  const q = new URLSearchParams({ limit: String(limit) });
  if (status) q.set("status", status);
  const data = await hubFetch<{ items: CrossDeptItem[] }>(`/cross-dept/queue?${q}`);
  return Array.isArray(data.items) ? data.items : [];
}

export async function emitCrossDeptProject(input: {
  title: string;
  project_id?: string;
}): Promise<{ emitted: boolean; event_id?: string; queued?: CrossDeptItem[] }> {
  return hubFetch("/cross-dept/emit-project", {
    method: "POST",
    body: JSON.stringify({
      title: input.title,
      project_id: input.project_id || null,
      source_agent: "ceo",
    }),
    timeoutMs: 15_000,
  });
}

export async function drainCrossDeptQueue(limit = 3): Promise<{
  processed: number;
  ok: number;
  failed: number;
  llm_enabled?: boolean;
}> {
  return hubFetch("/cross-dept/drain", {
    method: "POST",
    body: JSON.stringify({ limit }),
    timeoutMs: 120_000,
  });
}
