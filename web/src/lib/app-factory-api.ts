import { hubApiUrl } from "./hub-api-config";
import type { AppBranch } from "./apps-api";

export type FactoryStack = "nextjs" | "expo";

export interface AppFactoryRequest {
  name: string;
  brief: string;
  stack?: FactoryStack;
  slug?: string;
  github_repo?: string;
  local_path?: string;
  branch?: AppBranch;
  auto_run_pipeline?: boolean;
  dry_run?: boolean;
}

export interface FactoryIssue {
  number: number;
  title: string;
  url: string;
  agent_ready: boolean;
}

export interface AppFactoryRun {
  run_id: string;
  status: string;
  progress: number;
  log: string[];
  slug?: string;
  plan?: Array<Record<string, unknown>>;
  issues?: FactoryIssue[];
  app?: Record<string, unknown>;
  pipeline?: Record<string, unknown>;
  error?: string;
  started_at?: string;
}

async function factoryFetch<T>(path: string, init?: RequestInit): Promise<T> {
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
    throw new Error(body || `Factory error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function startAppFactory(
  body: AppFactoryRequest
): Promise<{ run_id: string; status: string; slug: string }> {
  return factoryFetch("/apps/factory", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchAppFactoryRun(runId: string): Promise<AppFactoryRun> {
  return factoryFetch(`/apps/factory/runs/${encodeURIComponent(runId)}`);
}

export async function fetchAppFactoryRuns(): Promise<{
  runs: AppFactoryRun[];
  count: number;
}> {
  return factoryFetch("/apps/factory/runs");
}

export async function triggerFactoryPipeline(
  runId: string
): Promise<Record<string, unknown>> {
  return factoryFetch(
    `/apps/factory/runs/${encodeURIComponent(runId)}/pipeline`,
    { method: "POST" }
  );
}
