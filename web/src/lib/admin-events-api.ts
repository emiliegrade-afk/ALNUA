import { hubFetch } from "./hub-fetch";

export interface HubEvent {
  event_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  source_agent: string;
  ts: number;
  handled_by?: string[];
}

export interface EventStats {
  total_events_in_memory: number;
  by_type: Record<string, number>;
  by_source_agent: Record<string, number>;
  registered_handlers: Record<string, number>;
  available_event_types: Record<string, string>;
}

export async function fetchRecentEvents(options?: {
  eventType?: string;
  sourceAgent?: string;
  limit?: number;
}): Promise<HubEvent[]> {
  const params = new URLSearchParams();
  if (options?.eventType) params.set("event_type", options.eventType);
  if (options?.sourceAgent) params.set("source_agent", options.sourceAgent);
  if (options?.limit) params.set("limit", String(options.limit));
  const q = params.toString() ? `?${params}` : "";
  return hubFetch<HubEvent[]>(`/services/events/recent${q}`, { timeoutMs: 10_000 });
}

export async function fetchEventStats(): Promise<EventStats> {
  return hubFetch<EventStats>("/services/events/stats", { timeoutMs: 8_000 });
}

export async function fetchEventTypes(): Promise<Record<string, string>> {
  return hubFetch<Record<string, string>>("/services/events/types", { timeoutMs: 8_000 });
}

export async function clearEventStore(): Promise<{ status: string }> {
  return hubFetch<{ status: string }>("/services/events/clear", {
    method: "POST",
    timeoutMs: 8_000,
  });
}
