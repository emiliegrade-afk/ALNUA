import type { Project } from "./types";
import { hubFetch } from "./hub-fetch";

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
  return hubFetch("/agents/brainstorm/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      project_id: projectId,
      session_id: sessionId,
    }),
  });
}

export async function fetchBrainstormSessions(): Promise<BrainstormSession[]> {
  return hubFetch<BrainstormSession[]>("/brainstorm/sessions");
}

export async function fetchBrainstormSession(
  sessionId: string
): Promise<BrainstormSessionDetail> {
  return hubFetch<BrainstormSessionDetail>(`/brainstorm/sessions/${sessionId}`);
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
  return hubFetch<SummarizeResult>(
    `/brainstorm/sessions/${sessionId}/summarize`,
    { method: "POST", timeoutMs: 120_000 }
  );
}

export async function fetchSessionSummary(
  sessionId: string
): Promise<{ summary: string; title: string; file_path?: string }> {
  const data = await hubFetch<{
    summary: string;
    title: string;
    file_path?: string;
  }>(`/brainstorm/sessions/${sessionId}/summary`);
  return data;
}

export async function revealSummaryFile(filePath: string): Promise<void> {
  await hubFetch("/brainstorm/summaries/reveal", {
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
  return hubFetch("/roadmap", {
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
  return hubFetch<Project[]>("/projects");
}

export type { Project };
