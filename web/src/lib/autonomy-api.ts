import { hubFetch } from "@/lib/hub-fetch";

export interface GateCriterion {
  id: string;
  label: string;
  critical: boolean;
  phase: number;
  passed: boolean;
}

export interface AcademyGate {
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
  academy_gate: AcademyGate;
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
  };
}

export async function fetchCeoCockpit(): Promise<CeoCockpit> {
  return hubFetch<CeoCockpit>("/autonomy/ceo-cockpit");
}

export async function fetchAcademyGate(refresh = true): Promise<AcademyGate> {
  return hubFetch<AcademyGate>(`/autonomy/academy-gate?refresh=${refresh}`);
}

export async function evaluateAcademyGate(): Promise<AcademyGate & { message: string }> {
  return hubFetch("/autonomy/academy-gate/evaluate", { method: "POST" });
}
