import { hubFetch } from "./hub-fetch";

/** Entonnoir de conversion Marketing (Phase 37, ROADMAP.md) — saisie
 * mensuelle manuelle par produit (Visiteurs → Intéressés → Engagés →
 * Abonnés → Clients). Aucun tracking automatique côté Hub aujourd'hui :
 * la source réelle vit dans les analytics propres à chaque produit
 * (App Store Connect, Play Console, Plausible/GA4, signups Supabase). */

export interface FunnelSnapshot {
  id: string;
  project_id: string;
  period_month: string;
  visitors: number;
  interested: number;
  engaged: number;
  subscribers: number;
  customers: number;
  source_note: string | null;
  entered_by_agent_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface FunnelSnapshotInput {
  project_id: string;
  period_month: string;
  visitors: number;
  interested: number;
  engaged: number;
  subscribers: number;
  customers: number;
  source_note?: string | null;
  entered_by_agent_id?: string | null;
}

export function fetchLatestFunnelSnapshot(projectId: string): Promise<FunnelSnapshot | null> {
  return hubFetch(`/marketing/funnel/latest?project_id=${encodeURIComponent(projectId)}`);
}

export function fetchFunnelSnapshots(projectId?: string): Promise<FunnelSnapshot[]> {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return hubFetch(`/marketing/funnel${qs}`);
}

export function upsertFunnelSnapshot(body: FunnelSnapshotInput): Promise<FunnelSnapshot> {
  return hubFetch("/marketing/funnel", { method: "POST", body: JSON.stringify(body) });
}
