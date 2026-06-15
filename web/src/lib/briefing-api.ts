import { hubFetch } from "./hub-fetch";

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
  unified?: boolean;
  orchestration?: Record<string, unknown>;
}

export interface BriefingBadge {
  has_urgent: boolean;
  urgent_count: number;
  pending_count: number;
}

export interface CooBrief {
  headline?: string;
  priority_1?: string;
  priority_2?: string;
  priority_3?: string;
  alerts?: string[];
  opportunities?: string[];
  team_performance?: string;
  recommended_focus?: string;
}

export interface CooDailyBriefing {
  date: string;
  context: string;
  duration_ms: number;
  coo_brief: CooBrief;
  raw_data: {
    leaderboard?: Record<string, unknown>;
    costs?: Record<string, unknown>;
    events?: Record<string, unknown>;
    trends_collected?: boolean;
    memory_health?: Record<string, unknown>;
  };
}

export interface FetchTodayBriefingOptions {
  ensure?: boolean;
  timeoutMs?: number;
}

async function briefingFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  return hubFetch<T>(path, { timeoutMs: 8_000, ...options });
}

export async function fetchTodayBriefing(
  options?: FetchTodayBriefingOptions
): Promise<DailyBriefing> {
  const ensure = options?.ensure ?? false;
  const timeoutMs = options?.timeoutMs ?? (ensure ? 90_000 : 8_000);
  return briefingFetch<DailyBriefing>(
    `/briefing/today?ensure=${ensure ? "true" : "false"}`,
    { timeoutMs }
  );
}

export async function fetchBriefingBadge(): Promise<BriefingBadge | null> {
  try {
    const briefing = await fetchTodayBriefing({ ensure: false, timeoutMs: 5_000 });
    return briefingToBadge(briefing);
  } catch {
    return null;
  }
}

export async function fetchBriefingHistory(limit = 30): Promise<DailyBriefing[]> {
  return briefingFetch<DailyBriefing[]>(`/briefing/history?limit=${limit}`, {
    timeoutMs: 15_000,
  });
}

export async function generateBriefingNow(): Promise<DailyBriefing> {
  return briefingFetch<DailyBriefing>("/briefing/generate", {
    method: "POST",
    timeoutMs: 180_000,
  });
}

export async function fetchCooDailyBriefing(context = ""): Promise<CooDailyBriefing> {
  return hubFetch<CooDailyBriefing>("/services/briefing/daily", {
    method: "POST",
    body: JSON.stringify({
      context,
      include_trends: true,
      include_costs: true,
      include_events: true,
    }),
    timeoutMs: 180_000,
  });
}

export function briefingToBadge(briefing: DailyBriefing): BriefingBadge {
  return {
    has_urgent: briefing.has_urgent,
    urgent_count: briefing.urgent_count,
    pending_count: briefing.pending_count,
  };
}
