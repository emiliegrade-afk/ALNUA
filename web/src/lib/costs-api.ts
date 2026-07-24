import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";
import { parseHubApiError } from "./hub-api-error";

async function costsFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(hubApiUrl(path), {
    ...init,
    headers: {
      ...hubApiKeyHeaders(),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(parseHubApiError(text, res.status));
  }
  return res.json() as Promise<T>;
}

export interface CombinedCostsReport {
  period_days: number;
  llm: { total_cost_usd: number; total_calls: number };
  elevenlabs: {
    configured: boolean;
    reachable?: boolean;
    message?: string;
    tier?: string;
    character_count?: number;
    character_limit?: number;
    pct_used?: number;
    reset_date?: string | null;
    monthly_plan_cost_usd?: number | null;
    estimated_cost_this_period_usd?: number | null;
  };
  manual: {
    entries: Array<{
      id: string;
      source: string;
      amount_usd: number;
      period: string;
      note: string;
      recorded_at: string;
    }>;
    total_usd: number;
    by_source: Record<string, number>;
  };
  total_usd_estimate: number;
}

export async function fetchCombinedCosts(days = 30): Promise<CombinedCostsReport> {
  return costsFetch(`/services/costs/combined?days=${days}`);
}

export async function recordManualCost(
  source: string,
  amountUsd: number,
  note = "",
): Promise<{ id: string }> {
  return costsFetch("/services/costs/manual", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source, amount_usd: amountUsd, note }),
  });
}

export async function deleteManualCost(entryId: string): Promise<{ deleted: boolean }> {
  return costsFetch(`/services/costs/manual/${encodeURIComponent(entryId)}`, {
    method: "DELETE",
  });
}

export async function setElevenLabsPlanCost(usdPerMonth: number): Promise<void> {
  await costsFetch("/services/costs/elevenlabs/plan-cost", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usd_per_month: usdPerMonth }),
  });
}
