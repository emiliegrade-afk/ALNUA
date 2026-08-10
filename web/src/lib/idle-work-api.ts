import { hubFetch } from "./hub-fetch";

export type IdleItemLevel = 0 | 1 | 2 | 3;

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
  autonomy_level?: number;
  items: IdleQueueItem[];
  updated_at?: string;
}

export async function fetchIdleQueue(): Promise<IdleDayQueue> {
  return hubFetch<IdleDayQueue>("/workflows/idle/queue");
}

export async function validateIdleQueue(validated = true): Promise<IdleDayQueue> {
  return hubFetch<IdleDayQueue>("/workflows/idle/validate", {
    method: "POST",
    body: JSON.stringify({ validated }),
  });
}

export async function runIdlePlan(): Promise<Record<string, unknown>> {
  return hubFetch("/workflows/idle/plan", { method: "POST" });
}

export async function runIdleDrain(): Promise<Record<string, unknown>> {
  return hubFetch("/workflows/idle/drain", { method: "POST" });
}
