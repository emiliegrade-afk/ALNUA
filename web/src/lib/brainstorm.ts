import type { Project } from "./types";

import { hubApiKeyHeaders } from "./hub-api-key";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const timeoutMs = options?.timeoutMs ?? 30_000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const { timeoutMs: _timeout, ...fetchOptions } = options ?? {};
  void _timeout;

  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      headers: hubApiKeyHeaders({
        "Content-Type": "application/json",
        ...fetchOptions?.headers,
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

export interface BrainstormMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

export interface BrainstormSession {
  session_id: string;
  title: string;
  project_id: string | null;
  project_name?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  has_summary?: boolean;
  summary_title?: string;
  summary_number?: number;
  summary_file_path?: string;
}

export interface BrainstormSessionDetail {
  session_id: string;
  project_id: string | null;
  messages: BrainstormMessage[];
}

export const WELCOME_MESSAGE =
  "Bonjour Emilie. Sur quoi tu veux brainstormer aujourd'hui ? Je peux t'aider à explorer des idées de features, de nouveaux produits, des mécaniques de jeu, ou n'importe quelle direction stratégique pour ALNUA.";

export async function sendBrainstormMessage(
  message: string,
  projectId: string | null,
  sessionId: string | null
): Promise<{ response: string; session_id: string }> {
  return apiFetch("/agents/brainstorm/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      project_id: projectId,
      session_id: sessionId,
    }),
  });
}

export async function fetchBrainstormSessions(): Promise<BrainstormSession[]> {
  return apiFetch<BrainstormSession[]>("/brainstorm/sessions");
}

export async function fetchBrainstormSession(
  sessionId: string
): Promise<BrainstormSessionDetail> {
  return apiFetch<BrainstormSessionDetail>(`/brainstorm/sessions/${sessionId}`);
}

export interface SummarizeResult {
  summary_md: string;
  file_path: string;
  session_number: number;
  title: string;
  project_slug?: string;
  id?: string;
}

export async function summarizeBrainstormSession(
  sessionId: string
): Promise<SummarizeResult> {
  return apiFetch<SummarizeResult>(
    `/brainstorm/sessions/${sessionId}/summarize`,
    { method: "POST", timeoutMs: 120_000 }
  );
}

export async function fetchSessionSummary(
  sessionId: string
): Promise<{ summary: string; title: string; file_path?: string }> {
  const data = await apiFetch<{
    summary: string;
    title: string;
    file_path?: string;
  }>(`/brainstorm/sessions/${sessionId}/summary`);
  return data;
}

export async function revealSummaryFile(filePath: string): Promise<void> {
  await apiFetch("/brainstorm/summaries/reveal", {
    method: "POST",
    body: JSON.stringify({ file_path: filePath }),
  });
}

export async function createRoadmapItem(data: {
  project_id: string;
  title: string;
  description: string;
  priority?: "low" | "medium" | "high" | "critical";
  phase?: string;
  status?: "idea" | "planned";
}): Promise<unknown> {
  return apiFetch("/roadmap", {
    method: "POST",
    body: JSON.stringify({
      project_id: data.project_id,
      title: data.title,
      description: data.description,
      priority: data.priority ?? "medium",
      phase: data.phase ?? "brainstorm",
      status: data.status ?? "idea",
    }),
  });
}

export async function fetchProjects(): Promise<Project[]> {
  return apiFetch<Project[]>("/projects");
}

export type { Project };
