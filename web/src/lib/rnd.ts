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
  incubator_stage?: IncubatorStage;
  db_id?: string | null;
  created_at?: string;
  evaluated_at?: string;
}

export type IncubatorStage = "idee" | "prototype" | "validation" | "mvp" | "projet" | "departement";

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
  // `inbox_only` doit toujours être envoyé explicitement : l'omettre ne
  // désactive pas le filtre, le backend retombe sur son propre défaut
  // (`inbox_only=True`) — bug réel trouvé le 2026-07-31 (Pipeline
  // n'affichait qu'un sous-ensemble "inbox" au lieu du pipeline complet
  // malgré fetchRndIdeas(undefined, false)).
  const params = new URLSearchParams({ limit: "100", inbox_only: inboxOnly ? "true" : "false" });
  if (verdict) params.set("verdict", verdict);
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

/* Incubateur (Phase 24, ROADMAP.md) — Kanban Idée→Prototype→Validation→MVP→
   Projet→Département. `departement` n'est jamais envoyé ici (rejeté côté
   API, 400) : c'est un vrai geste d'approbation CEO, voir
   promoteIdeaToDepartment. */
export async function updateIncubatorStage(
  ideaId: string,
  stage: Exclude<IncubatorStage, "departement">
): Promise<{ idea_id: string; incubator_stage: IncubatorStage }> {
  return hubFetch(`/rnd/ideas/${encodeURIComponent(ideaId)}/incubator-stage`, {
    method: "PATCH",
    body: JSON.stringify({ stage }),
  });
}

export interface PromoteToDepartmentResult {
  dossier_id: string;
  dispatch: {
    message?: string;
    project_id?: string;
    roadmap_items?: unknown[];
  };
}

export async function promoteIdeaToDepartment(ideaId: string): Promise<PromoteToDepartmentResult> {
  return hubFetch(`/rnd/ideas/${encodeURIComponent(ideaId)}/incubator/promote-to-department`, {
    method: "POST",
  });
}

/* Recherche approfondie par thème (services/deep_research.py) — pipeline
   multi-rounds existant côté backend, jamais branché sur aucune UI R&D
   (ni /rd, ni rnd-v2) avant ce câblage. Endpoint générique hors /rnd, mais
   thématiquement R&D — client regroupé ici plutôt que dans un fichier à
   part pour une seule fonction. */
export interface DeepResearchFinding {
  finding: string;
  confidence: string;
  source: string;
}

export interface DeepResearchReport {
  query: string;
  agent_id: string;
  rounds_completed: number;
  depth: "quick" | "standard" | "deep";
  executive_summary: string;
  key_findings: DeepResearchFinding[];
  verified_claims: string[];
  unverified_claims: string[];
  knowledge_gaps: string[];
  recommended_actions: string[];
  generated_at: string;
}

export async function runDeepResearch(params: {
  query: string;
  context?: string;
  rounds?: number;
  agent_id?: "brainstorm" | "rnd_agent" | "analyst_business";
}): Promise<DeepResearchReport> {
  return hubFetch("/services/deep-research/run", {
    method: "POST",
    body: JSON.stringify({
      query: params.query,
      context: params.context ?? "",
      rounds: params.rounds ?? 2,
      agent_id: params.agent_id ?? "brainstorm",
    }),
    timeoutMs: 150_000,
  });
}
