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

export interface WorkflowRunSubject {
  kind: string;
  label: string;
  blurb?: string;
  dossier_id?: string;
  slug?: string;
  ticket_id?: string;
  href?: string;
}

export interface WorkflowRunSummary {
  run_id: string;
  recipe_id: string;
  status: string;
  blocked_at_step: string | null;
  created_at: string;
  finished_at: string | null;
  summary: string;
  subject?: WorkflowRunSubject;
  context_keys?: string[];
  steps_a_verifier?: {
    step_id: string;
    label: string;
    detail: string;
    gaps?: string[];
  }[];
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

export function fetchWorkflowRunsWaiting(
  limit = 20,
): Promise<{ runs: WorkflowRunSummary[] }> {
  return wfFetch(`/workflows/runs?limit=${limit}&waiting=a_verifier`);
}

export function approveWorkflowStep(
  runId: string,
  stepId: string,
  approverAgentId = "ceo",
): Promise<WorkflowRunResult> {
  return wfFetch(`/workflows/runs/${runId}/approve-step`, {
    method: "POST",
    body: JSON.stringify({ step_id: stepId, approver_agent_id: approverAgentId }),
  });
}

export function rejectWorkflowStep(
  runId: string,
  stepId: string,
  reason = "",
  rejectorAgentId = "ceo",
): Promise<WorkflowRunResult & { rejected?: boolean; ok?: boolean }> {
  return wfFetch(`/workflows/runs/${runId}/reject-step`, {
    method: "POST",
    body: JSON.stringify({
      step_id: stepId,
      rejector_agent_id: rejectorAgentId,
      reason,
    }),
  });
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
