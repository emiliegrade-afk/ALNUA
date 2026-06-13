import { hubApiUrl } from "./hub-api-config";

export interface ApiHealthStatus {
  online: boolean;
  authenticated: boolean;
}

const CACHE_TTL_MS = 120_000;
const DEFAULT_TIMEOUT_MS = 30_000;
const MAX_ATTEMPTS = 6;
const RETRY_DELAY_MS = 2_000;

let memoryCache: { at: number; status: ApiHealthStatus } | null = null;

export function getHubHealthCache(): ApiHealthStatus | null {
  if (!memoryCache) return null;
  if (Date.now() - memoryCache.at > CACHE_TTL_MS) return null;
  return memoryCache.status;
}

function setHubHealthCache(status: ApiHealthStatus): void {
  if (status.online && status.authenticated) {
    memoryCache = { at: Date.now(), status };
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** One round-trip via the Next.js proxy — validates backend + Hub key injection. */
export async function probeHubApi(
  timeoutMs = DEFAULT_TIMEOUT_MS
): Promise<ApiHealthStatus> {
  const offline: ApiHealthStatus = { online: false, authenticated: false };

  try {
    const res = await fetch(hubApiUrl("/projects"), {
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });

    if (res.status === 502) return offline;
    if (res.status === 503) return { online: true, authenticated: false };
    if (res.status === 401) return { online: true, authenticated: false };
    if (res.ok) return { online: true, authenticated: true };
    return offline;
  } catch {
    return offline;
  }
}

/** Cached health with retries — avoids false "offline" during Next.js cold compiles. */
export async function checkApiHealth(options?: {
  force?: boolean;
}): Promise<ApiHealthStatus> {
  if (!options?.force) {
    const cached = getHubHealthCache();
    if (cached) return cached;
  }

  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    const status = await probeHubApi();
    if (status.online && status.authenticated) {
      setHubHealthCache(status);
      return status;
    }
    // Config error — don't retry (missing HUB_API_KEY on Next server).
    if (status.online && !status.authenticated) {
      return status;
    }
    if (attempt < MAX_ATTEMPTS - 1) {
      await sleep(RETRY_DELAY_MS);
    }
  }

  return probeHubApi();
}

/** Background refresh — never blocks UI with a false negative. */
export function refreshHubHealthInBackground(): void {
  void probeHubApi().then((status) => {
    if (status.online && status.authenticated) {
      setHubHealthCache(status);
    }
  });
}
