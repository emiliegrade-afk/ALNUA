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
