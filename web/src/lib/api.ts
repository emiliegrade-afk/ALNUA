import type { Project, Ticket } from "./types";
import { hubFetch } from "./hub-fetch";

export type { ApiHealthStatus } from "./hub-health";
export { checkApiHealth } from "./hub-health";

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
  return hubFetch<COOInstructionResult>("/agents/coo/instruction", {
    method: "POST",
    body: JSON.stringify({ instruction, project: project ?? null }),
    timeoutMs: 120_000,
  });
}

export async function fetchProjects(): Promise<Project[]> {
  return hubFetch<Project[]>("/projects");
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
  return hubFetch<Project>("/projects", {
    method: "POST",
    body: JSON.stringify({
      name: data.name,
      branch: data.branch,
      description: data.description ?? "",
      status: data.status ?? "dev",
    }),
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  await hubFetch<{ ok: string }>(`/projects/${encodeURIComponent(projectId)}`, {
    method: "DELETE",
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
  return hubFetch<Ticket[]>(`/tickets${qs ? `?${qs}` : ""}`);
}
