import { hubApiKeyHeaders } from "./hub-api-key";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export interface BriefingTicket {
  id: string;
  title: string;
  priority: string;
  status: string;
  project_id: string;
  project_name?: string;
}

export interface BriefingPost {
  id: string;
  platform: string;
  text_content: string;
  project_id: string;
  project_name?: string;
}

export interface BriefingRoadmapItem {
  id: string;
  title: string;
  due_date: string;
  status: string;
  project_id: string;
  project_name?: string;
}

export interface BriefingRawData {
  tickets: BriefingTicket[];
  posts: BriefingPost[];
  roadmap: BriefingRoadmapItem[];
  dev_log: Array<{
    id: string;
    content: string;
    date: string;
    project_name?: string;
  }>;
  analytics_anomalies: Array<{
    project_name: string;
    metric_name: string;
    drop_pct: number;
  }>;
}

export interface DailyBriefing {
  id: string;
  date: string;
  summary: string;
  raw_data: BriefingRawData;
  has_urgent: boolean;
  urgent_count: number;
  pending_count: number;
  created_at: string;
}

export interface BriefingBadge {
  has_urgent: boolean;
  urgent_count: number;
  pending_count: number;
}

async function briefingFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  const { timeoutMs = 60_000, ...fetchOptions } = options ?? {};
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      headers: hubApiKeyHeaders({
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      }),
      cache: "no-store",
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`API ${res.status}: ${text}`);
    }

    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error("API timeout — le serveur met trop de temps à répondre.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchTodayBriefing(): Promise<DailyBriefing> {
  return briefingFetch<DailyBriefing>("/briefing/today");
}

export async function fetchBriefingHistory(
  limit = 30
): Promise<DailyBriefing[]> {
  return briefingFetch<DailyBriefing[]>(`/briefing/history?limit=${limit}`);
}

export async function generateBriefingNow(): Promise<DailyBriefing> {
  return briefingFetch<DailyBriefing>("/briefing/generate", {
    method: "POST",
    timeoutMs: 90_000,
  });
}

export function briefingToBadge(briefing: DailyBriefing): BriefingBadge {
  return {
    has_urgent: briefing.has_urgent,
    urgent_count: briefing.urgent_count,
    pending_count: briefing.pending_count,
  };
}
