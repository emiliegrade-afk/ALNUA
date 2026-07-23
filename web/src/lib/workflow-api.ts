import { hubApiUrl } from "./hub-api-config";

export type WorkflowStepStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "OK"
  | "A_VERIFIER"
  | "ECART";

export interface WorkflowRecipe {
  id: string;
  name: string;
  description: string;
  head_agent: string;
  steps: { id: string; label: string; head_agent: string }[];
  priority: string;
}

export interface WorkflowRunSummary {
  run_id: string;
  recipe_id: string;
  status: string;
  blocked_at_step: string | null;
  created_at: string;
  finished_at: string | null;
  summary: string;
}

export interface WorkflowRunResult {
  success: boolean;
  blocked: boolean;
  run_id: string;
  recipe_id: string;
  status: string;
  blocked_at_step: string | null;
  summary: string;
  steps: {
    step_id: string;
    label: string;
    status: WorkflowStepStatus;
    detail: string;
    gaps: string[];
  }[];
}

async function wfFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(hubApiUrl(path), {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Workflow API ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function fetchWorkflowRecipes(): Promise<WorkflowRecipe[]> {
  return wfFetch("/workflows/recipes");
}

export function fetchWorkflowRuns(limit = 20): Promise<{ runs: WorkflowRunSummary[] }> {
  return wfFetch(`/workflows/runs?limit=${limit}`);
}

export function runWorkflow(
  recipeId: string,
  context: Record<string, unknown> = {}
): Promise<WorkflowRunResult> {
  return wfFetch("/workflows/run", {
    method: "POST",
    body: JSON.stringify({ recipe_id: recipeId, context }),
  });
}

export function runOpsNow(): Promise<WorkflowRunResult> {
  return wfFetch("/workflows/ops/run", { method: "POST" });
}

export function runSemaineNow(): Promise<WorkflowRunResult> {
  return wfFetch("/workflows/semaine/run", { method: "POST" });
}

export function shipGameRelease(
  slug: string,
  targetStatus: "beta" | "prod" = "beta"
): Promise<WorkflowRunResult> {
  return wfFetch("/workflows/ship/game", {
    method: "POST",
    body: JSON.stringify({ slug, target_status: targetStatus }),
  });
}

export function shipRoboRelease(
  slug: string,
  targetStatus: "beta" | "prod" = "beta"
): Promise<WorkflowRunResult> {
  return wfFetch("/workflows/ship/robo", {
    method: "POST",
    body: JSON.stringify({ slug, target_status: targetStatus }),
  });
}
