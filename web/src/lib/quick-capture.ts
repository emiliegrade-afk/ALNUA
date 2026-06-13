import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";

export type QuickCaptureType = "ticket" | "idea" | "roadmap" | "note";

export type QuickCapturePriority = "critical" | "high" | "medium" | "low";

export interface QuickCapturePayload {
  type: QuickCaptureType;
  content: string;
  project_id: string;
  priority?: QuickCapturePriority;
}

export interface QuickCaptureResponse {
  id: string;
  type: QuickCaptureType;
  redirect_url: string;
}

async function apiFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  const { timeoutMs = 30_000, ...fetchOptions } = options ?? {};
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
      throw new Error("API timeout — le serveur met trop de temps à répondre.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export async function quickCapture(
  payload: QuickCapturePayload
): Promise<QuickCaptureResponse> {
  return apiFetch<QuickCaptureResponse>("/quick-capture", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export const QUICK_CAPTURE_PROJECT_KEY = "alnua_quick_capture_project_id";

export const QUICK_CAPTURE_COUNT_KEY = "alnua_quick_capture_today";

export interface QuickCaptureDailyCount {
  date: string;
  count: number;
}

export function getTodayCaptureCount(): number {
  if (typeof window === "undefined") return 0;
  try {
    const raw = localStorage.getItem(QUICK_CAPTURE_COUNT_KEY);
    if (!raw) return 0;
    const parsed = JSON.parse(raw) as QuickCaptureDailyCount;
    const today = new Date().toISOString().slice(0, 10);
    return parsed.date === today ? parsed.count : 0;
  } catch {
    return 0;
  }
}

export function incrementTodayCaptureCount(): number {
  const today = new Date().toISOString().slice(0, 10);
  const current = getTodayCaptureCount();
  const next = current + 1;
  localStorage.setItem(
    QUICK_CAPTURE_COUNT_KEY,
    JSON.stringify({ date: today, count: next } satisfies QuickCaptureDailyCount)
  );
  return next;
}

export function getStoredProjectId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(QUICK_CAPTURE_PROJECT_KEY);
}

export function storeProjectId(projectId: string): void {
  localStorage.setItem(QUICK_CAPTURE_PROJECT_KEY, projectId);
}
