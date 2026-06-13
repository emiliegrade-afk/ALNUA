const DEFAULT_BACKEND = "http://localhost:8000";

/** Direct FastAPI origin — used by the Next.js /api/hub proxy only. */
export function hubBackendBaseUrl(): string {
  return (
    process.env.HUB_API_BACKEND_URL?.replace(/\/$/, "") ??
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
    DEFAULT_BACKEND
  );
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
