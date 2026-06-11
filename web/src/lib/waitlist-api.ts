const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export type WaitlistStatus = "waiting" | "notified" | "converted";
export type WaitlistSource =
  | "instagram"
  | "tiktok"
  | "bouche_a_oreille"
  | "reddit"
  | "autre"
  | "direct";

export interface WaitlistProjectInfo {
  project_id: string;
  project_name: string;
  project_slug: string;
  description: string;
  status: string;
}

export interface WaitlistEntry {
  id: string;
  project_id: string;
  project_name?: string;
  email: string;
  first_name: string | null;
  source: string | null;
  message: string | null;
  status: WaitlistStatus;
  notified_at: string | null;
  created_at: string;
}

export interface WaitlistJoinResult {
  position: number;
  total: number;
}

export interface WaitlistStats {
  total: number;
  this_week: number;
  by_source: Record<string, number>;
  by_status: Record<string, number>;
  timeline_7d: { date: string; count: number }[];
  per_project: {
    project_id: string;
    project_name: string;
    project_slug: string;
    total: number;
    this_week: number;
  }[];
}

export interface WaitlistNotifyResult {
  notified_count: number;
  preview_html: string;
}

async function waitlistFetch<T>(
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
      headers: {
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      },
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
      throw new Error("API timeout — réessaie dans un instant.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchWaitlistInfo(
  projectSlug: string
): Promise<WaitlistProjectInfo> {
  return waitlistFetch<WaitlistProjectInfo>(
    `/waitlist/info/${encodeURIComponent(projectSlug)}`
  );
}

export async function fetchWaitlistCount(projectSlug: string): Promise<number> {
  const data = await waitlistFetch<{ count: number }>(
    `/waitlist/count/${encodeURIComponent(projectSlug)}`
  );
  return data.count;
}

export async function joinWaitlist(body: {
  project_slug: string;
  email: string;
  first_name?: string;
  source?: string;
  message?: string;
}): Promise<WaitlistJoinResult> {
  return waitlistFetch<WaitlistJoinResult>("/waitlist/join", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchWaitlistEntries(params?: {
  project_id?: string;
  status?: string;
  source?: string;
}): Promise<WaitlistEntry[]> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.status) qs.set("status", params.status);
  if (params?.source) qs.set("source", params.source);
  const query = qs.toString();
  return waitlistFetch<WaitlistEntry[]>(`/waitlist${query ? `?${query}` : ""}`);
}

export async function fetchWaitlistStats(
  projectId?: string
): Promise<WaitlistStats> {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return waitlistFetch<WaitlistStats>(`/waitlist/stats${qs}`);
}

export async function notifyWaitlist(body: {
  project_id: string;
  subject: string;
  message_md: string;
  status_filter?: WaitlistStatus;
}): Promise<WaitlistNotifyResult> {
  return waitlistFetch<WaitlistNotifyResult>("/waitlist/notify", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function generateWaitlistEmail(
  projectId: string
): Promise<{ subject: string; message_md: string }> {
  return waitlistFetch("/waitlist/generate-email", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
    timeoutMs: 90_000,
  });
}

export async function updateWaitlistStatus(
  entryId: string,
  status: WaitlistStatus
): Promise<WaitlistEntry> {
  return waitlistFetch<WaitlistEntry>(`/waitlist/${entryId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function deleteWaitlistEntry(entryId: string): Promise<void> {
  await waitlistFetch<{ ok: boolean }>(`/waitlist/${entryId}`, {
    method: "DELETE",
  });
}

export function waitlistCsvUrl(projectId: string): string {
  return `${API_URL}/waitlist/export/${encodeURIComponent(projectId)}`;
}

export async function fetchWaitlistPageUrl(
  projectId: string
): Promise<{ page_url: string; project_slug: string }> {
  return waitlistFetch(`/waitlist/page-url/${encodeURIComponent(projectId)}`);
}
