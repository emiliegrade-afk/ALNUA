import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";

export type ReleaseStatus = "draft" | "published";

export interface Release {
  id: string;
  project_id: string;
  project_name?: string;
  version: string;
  release_date: string | null;
  app_store_notes: string | null;
  google_play_notes: string | null;
  changelog_md: string | null;
  dev_log_ids: string[] | null;
  status: ReleaseStatus;
  created_at: string;
}

export interface DevLogEntry {
  id: string;
  project_id: string;
  date: string;
  content: string;
  used_for_content: boolean;
  created_at: string;
}

async function releasesFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  const { timeoutMs = 60_000, ...fetchOptions } = options ?? {};
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(hubApiUrl(path), {
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
      throw new Error("Génération trop longue — réessaie dans un instant.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchReleases(projectId?: string): Promise<Release[]> {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return releasesFetch<Release[]>(`/releases${qs}`);
}

export async function fetchRelease(releaseId: string): Promise<Release> {
  return releasesFetch<Release>(`/releases/${releaseId}`);
}

export async function generateRelease(body: {
  project_id: string;
  version: string;
  since_date?: string;
  dev_log_ids?: string[];
}): Promise<Release> {
  return releasesFetch<Release>("/releases/generate", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 150_000,
  });
}

export async function updateRelease(
  releaseId: string,
  body: {
    app_store_notes?: string;
    google_play_notes?: string;
    changelog_md?: string;
    status?: ReleaseStatus;
    release_date?: string;
  }
): Promise<Release> {
  return releasesFetch<Release>(`/releases/${releaseId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deleteRelease(releaseId: string): Promise<void> {
  await releasesFetch<{ ok: boolean }>(`/releases/${releaseId}`, {
    method: "DELETE",
  });
}

export async function fetchDevLog(projectId: string): Promise<DevLogEntry[]> {
  return releasesFetch<DevLogEntry[]>(
    `/dev-log?project_id=${encodeURIComponent(projectId)}`
  );
}

export const APP_STORE_CHAR_LIMIT = 4000;
export const GOOGLE_PLAY_CHAR_LIMIT = 500;
