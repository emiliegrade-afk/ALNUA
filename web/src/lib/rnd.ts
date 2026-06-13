import { hubFetch } from "./hub-fetch";

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
  return hubFetch<RndIdea[]>(`/rnd/ideas${params}`);
}

export async function fetchRndIdea(ideaId: string): Promise<RndIdea> {
  return hubFetch<RndIdea>(`/rnd/ideas/${encodeURIComponent(ideaId)}`);
}

export async function fetchRndVision(): Promise<string> {
  const data = await hubFetch<{ vision: string }>("/rnd/vision");
  return data.vision;
}

export async function setRndVision(vision: string): Promise<void> {
  await hubFetch("/rnd/vision", {
    method: "POST",
    body: JSON.stringify({ vision }),
  });
}

export async function injectRndIdea(idea: string): Promise<RndIdea> {
  return hubFetch<RndIdea>("/rnd/inject", {
    method: "POST",
    body: JSON.stringify({ idea, source: "Emilie" }),
  });
}

export async function triggerRndCycle(): Promise<string> {
  const data = await hubFetch<{ status: string }>("/rnd/cycle", { method: "POST" });
  return data.status;
}

export async function fetchRndCompetitive(): Promise<RndCompetitive[]> {
  return hubFetch<RndCompetitive[]>("/rnd/competitive");
}
