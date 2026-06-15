import { hubFetch } from "@/lib/hub-fetch";

export interface GateCriterion {
  id: string;
  label: string;
  critical: boolean;
  phase: number;
  passed: boolean;
}

export interface NuawayGate {
  gate_open: boolean;
  readiness_pct: number;
  passed: number;
  total: number;
  critical_passed: number;
  critical_total: number;
  criteria: GateCriterion[];
  metrics: Record<string, unknown>;
  headline?: string;
  error?: string;
}

export interface CeoQueueItem {
  id: string;
  slug?: string;
  title: string;
  recommendation?: string;
  can_decide?: boolean;
}

export interface CeoCockpit {
  headline: string;
  nuaway_gate: NuawayGate;
  beta_readiness: BetaReadiness;
  academy: Record<string, unknown>;
  production_ops: Record<string, unknown>;
  ceo_queue: {
    to_validate: CeoQueueItem[];
    to_prepare: CeoQueueItem[];
    error?: string;
  };
  pipeline: {
    agent_ready_count: number;
    github_configured: boolean;
    nomad_repo: string | null;
  };
}

export interface BetaCriterion extends GateCriterion {
  category?: string;
}

export interface BetaReadiness {
  beta_ready: boolean;
  readiness_pct: number;
  passed: number;
  total: number;
  critical_passed: number;
  critical_total: number;
  criteria: BetaCriterion[];
  missing_critical?: string[];
  ceo_beta?: {
    approved?: boolean;
    note?: string;
    at?: string | null;
  };
  headline?: string;
  markdown?: string;
  error?: string;
}

export async function fetchCeoCockpit(): Promise<CeoCockpit> {
  return hubFetch<CeoCockpit>("/autonomy/ceo-cockpit");
}

export async function fetchNuawayGate(refresh = true): Promise<NuawayGate> {
  return hubFetch<NuawayGate>(`/autonomy/nuaway-gate?refresh=${refresh}`);
}

export async function evaluateNuawayGate(): Promise<NuawayGate & { message: string }> {
  return hubFetch("/autonomy/nuaway-gate/evaluate", { method: "POST" });
}

export async function fetchBetaReadiness(refresh = true): Promise<BetaReadiness> {
  return hubFetch<BetaReadiness>(`/autonomy/nuaway-readiness?refresh=${refresh}`);
}

export async function generateReadinessReport(): Promise<BetaReadiness & { message: string }> {
  return hubFetch("/autonomy/nuaway-readiness/report", { method: "POST" });
}

export async function setCeoBetaGo(
  approved: boolean,
  note = ""
): Promise<BetaReadiness & { message: string }> {
  return hubFetch("/autonomy/nuaway-readiness/ceo-go", {
    method: "POST",
    body: JSON.stringify({ approved, note }),
  });
}
