const DEFAULT_BACKEND = "http://127.0.0.1:8003";

/** Ports tried when HUB_API_BACKEND_URL is unset or backend is down (dev). */
export const HUB_BACKEND_FALLBACK_PORTS = [8003, 8002, 8000, 8001] as const;

/** Direct FastAPI origin — used by the Next.js /api/hub proxy only. */
export function hubBackendBaseUrl(): string {
  const configured = process.env.HUB_API_BACKEND_URL?.replace(/\/$/, "");
  if (configured) {
    return configured;
  }
  return DEFAULT_BACKEND;
}

/** Hub API prefix: browser → same-origin proxy; SSR → backend direct. */
export function hubApiBase(): string {
  if (typeof window !== "undefined") {
    return "/api/hub";
  }
  return hubBackendBaseUrl();
}

/** Build a full Hub API URL. Path must start with `/`. */
export function hubApiUrl(path: string): string {
  const base = hubApiBase().replace(/\/$/, "");
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalized}`;
}

/** Same-origin proxy URL for href/src/download in UI — avoids SSR/client hydration mismatch. */
export function hubPublicApiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `/api/hub${normalized}`;
}
