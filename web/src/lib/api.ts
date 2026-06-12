import type { Project, Ticket } from "./types";
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

export async function fetchBriefing(): Promise<string> {
  const data = await apiFetch<{ briefing: string }>("/agents/coo/briefing", {
    method: "POST",
    timeoutMs: 15_000,
  });
  return data.briefing;
}

export interface COOInstructionResult {
  response: string;
  issue_created: boolean;
  issue_number?: number;
  issue_url?: string;
  repo?: string;
}

export async function sendCOOInstruction(
  instruction: string,
  project?: string
): Promise<COOInstructionResult> {
  return apiFetch<COOInstructionResult>("/agents/coo/instruction", {
    method: "POST",
    body: JSON.stringify({ instruction, project: project ?? null }),
    timeoutMs: 120_000,
  });
}

export async function fetchProjects(): Promise<Project[]> {
  return apiFetch<Project[]>("/projects");
}

export interface ProjectCreatePayload {
  name: string;
  branch: Project["branch"];
  description?: string;
  status?: Project["status"];
}

export async function createProject(
  data: ProjectCreatePayload
): Promise<Project> {
  return apiFetch<Project>("/projects", {
    method: "POST",
    body: JSON.stringify({
      name: data.name,
      branch: data.branch,
      description: data.description ?? "",
      status: data.status ?? "dev",
    }),
  });
}

export async function fetchTickets(
  projectId?: string,
  status?: string
): Promise<Ticket[]> {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  if (status) params.set("status", status);
  const qs = params.toString();
  return apiFetch<Ticket[]>(`/tickets${qs ? `?${qs}` : ""}`);
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const data = await apiFetch<{ status: string }>("/health");
    return data.status === "ok";
  } catch {
    return false;
  }
}
