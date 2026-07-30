import type {
  TicketPriority,
  TicketStatus,
  TicketType,
} from "@/components/tickets/tickets.constants";
import type { Ticket } from "@/lib/types";
import { hubFetch } from "./hub-fetch";

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
  return hubFetch<TicketWithProject[]>(`/tickets${query ? `?${query}` : ""}`);
}

export interface CreateTicketPayload {
  title: string;
  type: TicketType;
  priority: TicketPriority;
  project_id: string;
  description?: string;
  source?: "emilie";
  assignee_agent_id?: string;
  story_points?: number;
  due_date?: string;
}

export async function createTicket(
  data: CreateTicketPayload
): Promise<TicketWithProject> {
  return hubFetch<TicketWithProject>("/tickets", {
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
  assignee_agent_id?: string;
  story_points?: number;
  due_date?: string;
}

export async function updateTicket(
  id: string,
  data: UpdateTicketPayload
): Promise<TicketWithProject> {
  return hubFetch<TicketWithProject>(`/tickets/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function generateCursorPrompt(
  ticketId: string
): Promise<{ cursor_prompt: string; ticket: TicketWithProject }> {
  return hubFetch<{ cursor_prompt: string; ticket: TicketWithProject }>(
    `/tickets/${ticketId}/generate-cursor-prompt`,
    { method: "POST", timeoutMs: 120_000 }
  );
}

export async function createRoadmapFromTicket(
  ticketId: string
): Promise<import("@/lib/types").RoadmapItem> {
  return hubFetch(`/roadmap/from-ticket/${ticketId}`, {
    method: "POST",
  });
}

export function countOpenTickets(tickets: TicketWithProject[]): number {
  return tickets.filter((t) => t.status === "open").length;
}
