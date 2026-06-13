import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";
import { parseHubApiError } from "./hub-api-error";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(hubApiUrl(path), {
    ...options,
    headers: hubApiKeyHeaders({
      "Content-Type": "application/json",
      ...options?.headers,
    }),
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(parseHubApiError(text, res.status));
  }
  return res.json() as Promise<T>;
}

export interface RndIdea {
  id: string;
  title: string;
  description: string;
  source?: string;
  status?: string;
  score?: number | null;
  market_score?: number;
  feasibility_score?: number;
  vision_score?: number;
  verdict?: "GO" | "MAYBE" | "NO" | null;
  verdict_reason?: string;
  reasoning?: string;
  next_step?: string;
  why_now?: string;
  effort?: string;
  domain?: string;
  spec_file?: string;
  lifecycle_status?: string;
  dossier_id?: string | null;
  db_id?: string | null;
  created_at?: string;
  evaluated_at?: string;
}

export interface RndCompetitive {
  product?: string;
  app?: string;
  anti_patterns?: string[];
  timestamp?: string;
}

export async function fetchRndIdeas(verdict?: string): Promise<RndIdea[]> {
  const params = verdict ? `?verdict=${verdict}&limit=50` : "?limit=50";
  return apiFetch<RndIdea[]>(`/rnd/ideas${params}`);
}

export async function fetchRndIdea(ideaId: string): Promise<RndIdea> {
  return apiFetch<RndIdea>(`/rnd/ideas/${encodeURIComponent(ideaId)}`);
}

export async function fetchRndVision(): Promise<string> {
  const data = await apiFetch<{ vision: string }>("/rnd/vision");
  return data.vision;
}

export async function setRndVision(vision: string): Promise<void> {
  await apiFetch("/rnd/vision", {
    method: "POST",
    body: JSON.stringify({ vision }),
  });
}

export async function injectRndIdea(idea: string): Promise<RndIdea> {
  return apiFetch<RndIdea>("/rnd/inject", {
    method: "POST",
    body: JSON.stringify({ idea, source: "Emilie" }),
  });
}

export async function triggerRndCycle(): Promise<string> {
  const data = await apiFetch<{ status: string }>("/rnd/cycle", { method: "POST" });
  return data.status;
}

export async function fetchRndCompetitive(): Promise<RndCompetitive[]> {
  return apiFetch<RndCompetitive[]>("/rnd/competitive");
}
