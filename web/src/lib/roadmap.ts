import {
  normalizePriority,
  normalizeStatus,
} from "@/components/roadmap/roadmap.constants";
import type {
  RoadmapItem,
  RoadmapPriority,
  RoadmapStatus,
} from "@/lib/types";

function normalizeRoadmapItem(raw: RoadmapItem): RoadmapItem {
  return {
    ...raw,
    status: normalizeStatus(raw.status),
    priority: normalizePriority(raw.priority),
    phase: raw.phase ?? (raw as RoadmapItem & { sprint?: string }).sprint ?? null,
  };
}

import { hubApiKeyHeaders } from "./hub-api-key";

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
      headers: hubApiKeyHeaders({
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      }),
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

    if (res.status === 204) return undefined as T;
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

export interface FetchRoadmapParams {
  status?: RoadmapStatus;
  project_id?: string;
  priority?: RoadmapPriority[];
  phase?: string;
}

export async function fetchRoadmapItems(
  params: FetchRoadmapParams = {}
): Promise<RoadmapItem[]> {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.project_id) qs.set("project_id", params.project_id);
  params.priority?.forEach((p) => qs.append("priority", p));
  if (params.phase) qs.set("phase", params.phase);
  const query = qs.toString();
  const rows = await apiFetch<RoadmapItem[]>(
    `/roadmap${query ? `?${query}` : ""}`
  );
  return rows.map(normalizeRoadmapItem);
}

export interface CreateRoadmapPayload {
  title: string;
  description?: string;
  status?: RoadmapStatus;
  priority?: RoadmapPriority;
  project_id: string;
  phase?: string;
  due_date?: string;
}

export async function createRoadmapItem(
  data: CreateRoadmapPayload
): Promise<RoadmapItem> {
  const row = await apiFetch<RoadmapItem>("/roadmap", {
    method: "POST",
    body: JSON.stringify({
      title: data.title,
      description: data.description ?? "",
      status: data.status ?? "planned",
      priority: data.priority ?? "medium",
      project_id: data.project_id,
      phase: data.phase || undefined,
      due_date: data.due_date || undefined,
    }),
  });
  return normalizeRoadmapItem(row);
}

export interface UpdateRoadmapPayload {
  title?: string;
  description?: string;
  status?: RoadmapStatus;
  priority?: RoadmapPriority;
  project_id?: string;
  phase?: string;
  due_date?: string | null;
  linked_ticket_id?: string | null;
}

export async function updateRoadmapItem(
  id: string,
  data: UpdateRoadmapPayload
): Promise<RoadmapItem> {
  const row = await apiFetch<RoadmapItem>(`/roadmap/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
  return normalizeRoadmapItem(row);
}

export async function deleteRoadmapItem(id: string): Promise<void> {
  await apiFetch(`/roadmap/${id}`, { method: "DELETE" });
}

export function exportRoadmapCsv(items: RoadmapItem[]): void {
  const headers = [
    "id",
    "title",
    "description",
    "status",
    "priority",
    "phase",
    "due_date",
    "project_id",
    "project_name",
    "linked_ticket_id",
    "created_at",
  ];
  const escape = (v: string) => `"${v.replace(/"/g, '""')}"`;
  const rows = items.map((item) =>
    [
      item.id,
      item.title,
      item.description,
      item.status,
      item.priority,
      item.phase ?? "",
      item.due_date ?? "",
      item.project_id,
      item.project_name ?? "",
      item.linked_ticket_id ?? "",
      item.created_at,
    ]
      .map((v) => escape(String(v)))
      .join(",")
  );
  const csv = [headers.join(","), ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `roadmap-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
