import type { ModuleStatus, ProjectModule } from "@/lib/types";
import { hubFetch } from "./hub-fetch";

export async function fetchModules(projectId: string): Promise<ProjectModule[]> {
  return hubFetch<ProjectModule[]>(`/modules?project_id=${encodeURIComponent(projectId)}`);
}

export interface CreateModulePayload {
  project_id: string;
  name: string;
  status?: ModuleStatus;
  progress?: number;
  features_done?: number;
  features_total?: number;
  tests_passed_pct?: number;
  open_bugs?: number;
}

export async function createModule(data: CreateModulePayload): Promise<ProjectModule> {
  return hubFetch<ProjectModule>("/modules", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export interface UpdateModulePayload {
  name?: string;
  status?: ModuleStatus;
  progress?: number;
  features_done?: number;
  features_total?: number;
  tests_passed_pct?: number;
  open_bugs?: number;
}

export async function updateModule(id: string, data: UpdateModulePayload): Promise<ProjectModule> {
  return hubFetch<ProjectModule>(`/modules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteModule(id: string): Promise<void> {
  await hubFetch<{ status: string }>(`/modules/${id}`, { method: "DELETE" });
}
