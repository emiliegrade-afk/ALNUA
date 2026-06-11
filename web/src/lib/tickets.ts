import type {
  TicketPriority,
  TicketStatus,
  TicketType,
} from "@/components/tickets/tickets.constants";
import type { Ticket } from "@/lib/types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  const { timeoutMs = 30_000, ...fetchOptions } = options ?? {};
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      },
      cache: "no-store",
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      try {
        const json = JSON.parse(text) as { detail?: string };
        if (json.detail) throw new Error(json.detail);
      } catch (e) {
        if (e instanceof Error && e.message !== text) throw e;
      }
      throw new Error(`API ${res.status}: ${text}`);
    }

    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error("API timeout — le serveur met trop de temps à répondre.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export interface TicketWithProject extends Ticket {
  project_name?: string;
}

export interface FetchTicketsParams {
  project_id?: string;
  status?: TicketStatus;
  priority?: TicketPriority[];
  type?: TicketType[];
  limit?: number;
}

export async function fetchTicketsList(
  params: FetchTicketsParams = {}
): Promise<TicketWithProject[]> {
  const qs = new URLSearchParams();
  if (params.project_id) qs.set("project_id", params.project_id);
  if (params.status) qs.set("status", params.status);
  params.priority?.forEach((p) => qs.append("priority", p));
  params.type?.forEach((t) => qs.append("type", t));
  if (params.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return apiFetch<TicketWithProject[]>(`/tickets${query ? `?${query}` : ""}`);
}

export interface CreateTicketPayload {
  title: string;
  type: TicketType;
  priority: TicketPriority;
  project_id: string;
  description?: string;
  source?: "emilie";
}

export async function createTicket(
  data: CreateTicketPayload
): Promise<TicketWithProject> {
  return apiFetch<TicketWithProject>("/tickets", {
    method: "POST",
    body: JSON.stringify({
      ...data,
      source: "emilie",
      description: data.description ?? "",
    }),
  });
}

export interface UpdateTicketPayload {
  status?: TicketStatus;
  title?: string;
  description?: string;
  priority?: TicketPriority;
  cursor_prompt?: string;
}

export async function updateTicket(
  id: string,
  data: UpdateTicketPayload
): Promise<TicketWithProject> {
  return apiFetch<TicketWithProject>(`/tickets/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function generateCursorPrompt(
  ticketId: string
): Promise<{ cursor_prompt: string; ticket: TicketWithProject }> {
  return apiFetch<{ cursor_prompt: string; ticket: TicketWithProject }>(
    `/tickets/${ticketId}/generate-cursor-prompt`,
    { method: "POST", timeoutMs: 120_000 }
  );
}

export async function createRoadmapFromTicket(
  ticketId: string
): Promise<import("@/lib/types").RoadmapItem> {
  return apiFetch(`/roadmap/from-ticket/${ticketId}`, {
    method: "POST",
  });
}

export function countOpenTickets(tickets: TicketWithProject[]): number {
  return tickets.filter((t) => t.status === "open").length;
}
