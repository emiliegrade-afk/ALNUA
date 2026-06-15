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

export async function fetchRndIdeas(
  verdict?: string,
  inboxOnly = true
): Promise<RndIdea[]> {
  const params = new URLSearchParams({ limit: "50" });
  if (verdict) params.set("verdict", verdict);
  if (inboxOnly) params.set("inbox_only", "true");
  return hubFetch<RndIdea[]>(`/rnd/ideas?${params.toString()}`);
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

export interface RndUserSubmitSections {
  problem?: string;
  solution?: string;
  market?: string;
  mvp?: string;
  feasibility?: string;
  risks?: string;
}

export interface RndUserSubmitPayload {
  title: string;
  tagline?: string;
  domain?: string;
  why_now?: string;
  sections?: RndUserSubmitSections;
  enrich?: boolean;
}

export interface RndUserSubmitResponse {
  dossier: { id: string; slug: string; title: string };
  idea: RndIdea;
  message: string;
  enriching?: boolean;
}

export async function submitRndProposal(
  payload: RndUserSubmitPayload
): Promise<RndUserSubmitResponse> {
  return hubFetch<RndUserSubmitResponse>("/rnd/submit", {
    method: "POST",
    body: JSON.stringify({ ...payload, source: "Emilie" }),
  });
}

export async function triggerRndCycle(): Promise<string> {
  const data = await hubFetch<{ status: string }>("/rnd/cycle", { method: "POST" });
  return data.status;
}

export async function archiveRndIdea(ideaId: string): Promise<void> {
  await hubFetch(`/rnd/ideas/${encodeURIComponent(ideaId)}`, { method: "DELETE" });
}

export async function fetchRndCompetitive(): Promise<RndCompetitive[]> {
  return hubFetch<RndCompetitive[]>("/rnd/competitive");
}
