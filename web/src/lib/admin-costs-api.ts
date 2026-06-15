import { hubFetch } from "./hub-fetch";

export interface CostReport {
  period_days: number;
  agent_id_filter: string | null;
  total_calls: number;
  total_cost_usd: number;
  by_agent: Record<
    string,
    {
      calls: number;
      cost_usd: number;
      prompt_tokens: number;
      completion_tokens: number;
    }
  >;
  by_model: Record<string, { calls: number; cost_usd: number }>;
  by_day: Record<string, number>;
  most_expensive_agent: string | null;
}

export interface CostMonthlySummary {
  month: string;
  total_cost_usd: number;
  total_calls: number;
  by_agent: Record<string, number>;
  avg_cost_per_call_usd?: number;
  projection_30d_usd?: number;
}

export interface CostAlert {
  date: string;
  agent_id_filter: string | null;
  daily_budget_usd: number;
  spent_usd: number;
  remaining_usd: number;
  pct_used: number;
  alert: boolean;
  severity: "ok" | "warning" | "critical";
  calls_today: number;
}

export interface TopCostCall {
  agent_id: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  date: string;
  method: string;
  ts?: number;
}

export async function fetchCostReport(
  days = 7,
  agentId?: string
): Promise<CostReport> {
  const params = new URLSearchParams({ days: String(days) });
  if (agentId) params.set("agent_id", agentId);
  return hubFetch<CostReport>(`/services/costs/report?${params}`, { timeoutMs: 10_000 });
}

export async function fetchCostMonthly(month?: string): Promise<CostMonthlySummary> {
  const q = month ? `?month=${encodeURIComponent(month)}` : "";
  return hubFetch<CostMonthlySummary>(`/services/costs/monthly${q}`, { timeoutMs: 10_000 });
}

export async function fetchCostAlert(
  dailyBudgetUsd = 5
): Promise<CostAlert> {
  return hubFetch<CostAlert>(
    `/services/costs/alert?daily_budget_usd=${dailyBudgetUsd}`,
    { timeoutMs: 8_000 }
  );
}

export async function fetchTopCosts(
  limit = 10,
  days = 7
): Promise<TopCostCall[]> {
  return hubFetch<TopCostCall[]>(
    `/services/costs/top?limit=${limit}&days=${days}`,
    { timeoutMs: 10_000 }
  );
}
