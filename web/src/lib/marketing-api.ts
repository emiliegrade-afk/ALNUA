import { hubFetch } from "./hub-fetch";

/** Client dédié Marketing (Phase 29, ROADMAP.md) — jusqu'ici les actions
 * marketing passaient exclusivement par lib/pole-api.ts (générique
 * multi-pôles) ; ce fichier porte les lectures de données réelles du
 * cockpit (leaderboard compétition) qui n'avaient pas encore de client. */

export interface LeaderboardEntry {
  agent_id: string;
  first_name: string;
  last_name: string;
  team: string;
  score: number;
  rank: number;
  milestone_status: string;
}

export function fetchLeaderboard(month?: string): Promise<LeaderboardEntry[]> {
  return hubFetch(`/agents/leaderboard${month ? `?month=${encodeURIComponent(month)}` : ""}`);
}

// ---------------------------------------------------------------------------
// Campagnes (Phase 33, ROADMAP.md) — spent_usd est calculé côté backend en
// sommant les vraies transactions liées (campaign_id), jamais un ROI/reach
// fabriqué : campaign_roi_report reste un stub backend non exposé ici.
// ---------------------------------------------------------------------------
export type CampaignObjective = "awareness" | "traffic" | "conversions" | "engagement" | "video_views";
export type CampaignPlatform = "meta" | "google" | "tiktok";
export type CampaignStatus = "draft" | "active" | "paused" | "completed";

export interface Campaign {
  id: string;
  project_id: string | null;
  name: string;
  objective: CampaignObjective;
  platform: CampaignPlatform;
  status: CampaignStatus;
  budget_allocated_usd: number;
  spent_usd: number;
  audience: string | null;
  brief: string | null;
  start_date: string | null;
  end_date: string | null;
  created_by_agent_id: string | null;
  created_at: string;
  updated_at: string;
  // Stats de performance réelle (Phase 37) — saisie manuelle, null tant que
  // personne ne les a renseignées. roi_pct calculé côté backend uniquement
  // si revenue_generated_usd est saisi ET spent_usd > 0.
  reach: number | null;
  engagements: number | null;
  conversions: number | null;
  revenue_generated_usd: number | null;
  roi_pct: number | null;
  stats_updated_at: string | null;
}

export interface CampaignInput {
  name: string;
  objective: CampaignObjective;
  platform: CampaignPlatform;
  status?: CampaignStatus;
  budget_allocated_usd?: number;
  project_id?: string | null;
  audience?: string | null;
  brief?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface CampaignStatsInput {
  reach?: number;
  engagements?: number;
  conversions?: number;
  revenue_generated_usd?: number;
}

export interface PlatformPerformance {
  platform: CampaignPlatform;
  sample_size: number;
  reach: number;
  engagements: number;
  conversions: number;
  spent_usd: number;
  revenue_generated_usd: number | null;
  roi_pct: number | null;
}

export function fetchPerformanceByPlatform(): Promise<PlatformPerformance[]> {
  return hubFetch("/campaigns/performance-by-platform");
}

export function fetchCampaigns(filters?: {
  project_id?: string;
  status?: CampaignStatus;
  platform?: CampaignPlatform;
}): Promise<Campaign[]> {
  const qs = new URLSearchParams();
  if (filters?.project_id) qs.set("project_id", filters.project_id);
  if (filters?.status) qs.set("status", filters.status);
  if (filters?.platform) qs.set("platform", filters.platform);
  const query = qs.toString();
  return hubFetch(`/campaigns${query ? `?${query}` : ""}`);
}

export function createCampaign(body: CampaignInput): Promise<Campaign> {
  return hubFetch("/campaigns", { method: "POST", body: JSON.stringify(body) });
}

export function updateCampaign(
  id: string,
  body: Partial<CampaignInput> & Partial<CampaignStatsInput>
): Promise<Campaign> {
  return hubFetch(`/campaigns/${id}`, { method: "PATCH", body: JSON.stringify(body) });
}

export function deleteCampaign(id: string): Promise<{ ok: boolean }> {
  return hubFetch(`/campaigns/${id}`, { method: "DELETE" });
}
