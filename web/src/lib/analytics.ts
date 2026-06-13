import { hubFetch } from "./hub-fetch";

export type AnalyticsPeriod = "7d" | "30d" | "3m" | "6m" | "1y";

export type AnalyticsMetricName =
  | "downloads"
  | "active_users"
  | "subscriptions"
  | "mrr"
  | "churn"
  | "web_visitors";

export interface KpiValue {
  value: number | null;
  change_pct: number | null;
}

export interface AnalyticsSummary {
  downloads: KpiValue;
  subscriptions: KpiValue;
  mrr: KpiValue;
  churn: KpiValue;
  web_visitors: KpiValue;
  revenue_month: KpiValue;
}

export interface AnalyticsRow {
  id?: string;
  project_id: string;
  project_name?: string;
  metric_name: AnalyticsMetricName;
  value: number;
  date: string;
  source: string;
}

export interface RevenueMonth {
  month: string;
  revenue: number;
  expense: number;
  mrr: number;
}

export interface RevenueResponse {
  months: RevenueMonth[];
}

export interface FeedbackRow {
  id: string;
  project_id: string;
  project_name?: string;
  source: string;
  author: string | null;
  content: string;
  rating: number | null;
  sentiment: string;
  status: string;
  created_at: string;
}

export interface CreateMetricPayload {
  project_id: string;
  metric_name: AnalyticsMetricName;
  value: number;
  metric_date?: string;
  source?: string;
}

export async function fetchAnalyticsSummary(
  projectId?: string
): Promise<AnalyticsSummary> {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return hubFetch<AnalyticsSummary>(`/analytics/summary${qs}`);
}

export async function fetchAnalytics(params: {
  project_id?: string;
  metric_name?: AnalyticsMetricName;
  period?: AnalyticsPeriod;
}): Promise<AnalyticsRow[]> {
  const qs = new URLSearchParams();
  if (params.project_id) qs.set("project_id", params.project_id);
  if (params.metric_name) qs.set("metric_name", params.metric_name);
  if (params.period) qs.set("period", params.period);
  const query = qs.toString();
  return hubFetch<AnalyticsRow[]>(`/analytics${query ? `?${query}` : ""}`);
}

export async function fetchAnalyticsRevenue(params: {
  project_id?: string;
  period?: AnalyticsPeriod;
}): Promise<RevenueResponse> {
  const qs = new URLSearchParams();
  if (params.project_id) qs.set("project_id", params.project_id);
  if (params.period) qs.set("period", params.period);
  const query = qs.toString();
  return hubFetch<RevenueResponse>(
    `/analytics/revenue${query ? `?${query}` : ""}`
  );
}

export async function createAnalyticsMetric(
  data: CreateMetricPayload
): Promise<AnalyticsRow> {
  return hubFetch<AnalyticsRow>("/analytics", {
    method: "POST",
    body: JSON.stringify({
      project_id: data.project_id,
      metric_name: data.metric_name,
      value: data.value,
      date: data.metric_date,
      source: data.source,
    }),
  });
}

export async function fetchFeedback(params?: {
  project_id?: string;
  limit?: number;
}): Promise<FeedbackRow[]> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return hubFetch<FeedbackRow[]>(`/feedback${query ? `?${query}` : ""}`);
}

export function formatKpiValue(
  value: number | null | undefined,
  opts?: { suffix?: string; decimals?: number; isCurrency?: boolean }
): string {
  if (value === null || value === undefined) return "–";
  const decimals = opts?.decimals ?? (opts?.isCurrency ? 0 : 0);
  const formatted = opts?.isCurrency
    ? new Intl.NumberFormat("fr-FR", {
        style: "currency",
        currency: "EUR",
        maximumFractionDigits: decimals,
      }).format(value)
    : new Intl.NumberFormat("fr-FR", { maximumFractionDigits: decimals }).format(
        value
      );
  return opts?.suffix ? `${formatted}${opts.suffix}` : formatted;
}

export function formatChangePct(change: number | null | undefined): {
  text: string;
  positive: boolean | null;
} {
  if (change === null || change === undefined) {
    return { text: "", positive: null };
  }
  const sign = change > 0 ? "+" : "";
  return {
    text: `${sign}${change}%`,
    positive: change > 0 ? true : change < 0 ? false : null,
  };
}
