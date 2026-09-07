import { hubFetch } from "./hub-fetch";

export interface IdleQueueItem {
  id: string;
  level: number;
  kind: string;
  agent_id: string;
  title: string;
  family: string;
  status: string;
  payload?: Record<string, unknown>;
  run_id?: string | null;
  detail?: string;
  created_at?: string;
  finished_at?: string | null;
}

export interface IdleDayQueue {
  date: string;
  ceo_validated: boolean;
  validated_at?: string | null;
  tickets_promoted_at?: string | null;
  autonomy_level?: number;
  items: IdleQueueItem[];
  updated_at?: string;
  promote?: Record<string, unknown>;
}

export interface IdleDeliverableSummary {
  item_id: string;
  kind?: string;
  title?: string;
  agent_id?: string;
  status?: string;
  written_at?: string;
  preview?: string;
  path?: string;
}

export async function fetchIdleQueue(): Promise<IdleDayQueue> {
  return hubFetch<IdleDayQueue>("/workflows/idle/queue");
}

export async function validateIdleQueue(
  validated = true,
  promoteTickets = true,
): Promise<IdleDayQueue & { promote?: Record<string, unknown> }> {
  return hubFetch("/workflows/idle/validate", {
    method: "POST",
    body: JSON.stringify({ validated, promote_tickets: promoteTickets }),
  });
}

export async function runIdlePlan(): Promise<Record<string, unknown>> {
  return hubFetch("/workflows/idle/plan", { method: "POST" });
}

export async function runIdleDrain(): Promise<Record<string, unknown>> {
  return hubFetch("/workflows/idle/drain", { method: "POST" });
}

export async function fetchIdleDeliverables(limit = 20): Promise<IdleDeliverableSummary[]> {
  const data = await hubFetch<{ deliverables: IdleDeliverableSummary[] }>(
    `/workflows/idle/deliverables?limit=${limit}`,
  );
  return data.deliverables ?? [];
}

export async function fetchIdleDeliverable(itemId: string): Promise<Record<string, unknown>> {
  return hubFetch(`/workflows/idle/deliverables/${encodeURIComponent(itemId)}`);
}

export async function promoteIdleTickets(body?: {
  item_id?: string;
  project_id?: string;
  dry_run?: boolean;
}): Promise<Record<string, unknown>> {
  return hubFetch("/workflows/idle/promote-tickets", {
    method: "POST",
    body: JSON.stringify(body ?? {}),
  });
}
