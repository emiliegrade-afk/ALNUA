import { hubFetch } from "./hub-fetch";

export interface ABTestRunResult {
  name: string;
  winner: "A" | "B" | "tie";
  confidence: number;
  judge_reasoning: string;
  variant_a_label: string;
  variant_b_label: string;
  duration_ms: number;
  judgment?: {
    winner?: string;
    confidence?: number;
    reasoning?: string;
  };
  runs_a?: Array<{ success: boolean; error?: string }>;
  runs_b?: Array<{ success: boolean; error?: string }>;
}

export async function runQuickCompare(body: {
  agent_id: string;
  method: string;
  kwargs_a: Record<string, unknown>;
  kwargs_b: Record<string, unknown>;
  criteria?: string;
}): Promise<ABTestRunResult> {
  return hubFetch<ABTestRunResult>("/services/ab-test/quick-compare", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}

export async function runAbTest(body: {
  name: string;
  variant_a: {
    agent_id: string;
    method: string;
    kwargs: Record<string, unknown>;
    label?: string;
  };
  variant_b: {
    agent_id: string;
    method: string;
    kwargs: Record<string, unknown>;
    label?: string;
  };
  judge_criteria?: string;
  runs_per_variant?: number;
}): Promise<ABTestRunResult> {
  return hubFetch<ABTestRunResult>("/services/ab-test/run", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 180_000,
  });
}
