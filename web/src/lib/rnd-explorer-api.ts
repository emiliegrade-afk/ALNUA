import { hubFetch } from "./hub-fetch";

export interface ExplorerSignal {
  title: string;
  url: string;
  source: string;
  score: number;
  comments: number;
  category: string;
  fetched_at: string;
}

export interface ExplorerSignalsResponse {
  ok: boolean;
  mode: string;
  topics: string[];
  sources: string[];
  total: number;
  items: ExplorerSignal[];
  fetched_at: string;
  empty_reason: string | null;
}

export interface ExplorerBriefResponse {
  ok: boolean;
  mode: string;
  topics: string[];
  sources_used: string[];
  total_items?: number;
  items: ExplorerSignal[];
  synthesis: string;
  rnd_signals: string[];
  dossier_hooks: string[];
  agent_id?: string;
  error?: string;
  generated_at: string;
}

export function fetchExplorerSignals(params?: {
  topics?: string[];
  sources?: string[];
  limit?: number;
}) {
  const q = new URLSearchParams();
  if (params?.topics?.length) q.set("topics", params.topics.join(","));
  if (params?.sources?.length) q.set("sources", params.sources.join(","));
  if (params?.limit) q.set("limit", String(params.limit));
  const qs = q.toString();
  return hubFetch<ExplorerSignalsResponse>(
    `/rnd/explorer/signals${qs ? `?${qs}` : ""}`,
    { timeoutMs: 45_000 },
  );
}

export function fetchExplorerBrief(body: {
  topics?: string[];
  sources?: string[];
  agent_id?: string;
  limit?: number;
}) {
  return hubFetch<ExplorerBriefResponse>("/rnd/explorer/brief", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}
