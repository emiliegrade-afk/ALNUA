import { hubApiUrl } from "./hub-api-config";

export type AppBranch = "app" | "gaming" | "robotics" | "hub" | "other";

export interface AppRegistryEntry {
  slug: string;
  name: string;
  branch: AppBranch;
  github_repo: string;
  local_path: string;
  description: string;
  stack: string;
  prod_url: string;
  enabled: boolean;
  source: string;
  path_exists: boolean;
  github_configured: boolean;
}

export interface AppRegistrySummary {
  total: number;
  enabled: number;
  with_github: number;
  with_local_path: number;
  branches: Record<string, number>;
}

export interface AppRegistryResponse {
  summary: AppRegistrySummary;
  apps: AppRegistryEntry[];
}

export interface AppRegistryUpsert {
  slug: string;
  name: string;
  branch: AppBranch;
  github_repo?: string;
  local_path?: string;
  description?: string;
  stack?: string;
  prod_url?: string;
  enabled?: boolean;
}

async function registryFetch<T>(path: string, init?: RequestInit): Promise<T> {
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
    throw new Error(body || `Registry error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchAppRegistry(): Promise<AppRegistryResponse> {
  return registryFetch<AppRegistryResponse>("/apps/registry");
}

export async function upsertAppRegistry(
  body: AppRegistryUpsert
): Promise<AppRegistryEntry> {
  return registryFetch<AppRegistryEntry>("/apps/registry", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function deleteAppRegistry(slug: string): Promise<void> {
  await registryFetch<{ status: string }>(
    `/apps/registry/${encodeURIComponent(slug)}`,
    { method: "DELETE" }
  );
}
