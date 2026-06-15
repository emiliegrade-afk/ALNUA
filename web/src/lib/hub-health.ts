import { hubApiUrl } from "./hub-api-config";

export interface ApiHealthStatus {
  online: boolean;
  authenticated: boolean;
}

const CACHE_TTL_MS = 120_000;
const STALE_OK_TTL_MS = 30 * 60_000;
const DEFAULT_TIMEOUT_MS = 30_000;
const MAX_ATTEMPTS = 6;
const RETRY_DELAY_MS = 2_000;
const STORAGE_KEY = "alnua_hub_health_v1";

type CachedHealth = { at: number; status: ApiHealthStatus };

let memoryCache: CachedHealth | null = readStorageCache();
const listeners = new Set<(status: ApiHealthStatus) => void>();

function readStorageCache(): CachedHealth | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CachedHealth;
    if (
      typeof parsed?.at !== "number" ||
      typeof parsed?.status?.online !== "boolean" ||
      typeof parsed?.status?.authenticated !== "boolean"
    ) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function writeStorageCache(entry: CachedHealth): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(entry));
  } catch {
    // sessionStorage full or unavailable — memory cache still works
  }
}

function notifyListeners(status: ApiHealthStatus): void {
  listeners.forEach((listener) => listener(status));
}

function isFresh(entry: CachedHealth, ttlMs: number): boolean {
  return Date.now() - entry.at <= ttlMs;
}

function pickBestCache(): CachedHealth | null {
  const candidates = [memoryCache, readStorageCache()].filter(
    (entry): entry is CachedHealth => entry != null
  );
  if (candidates.length === 0) return null;
  return candidates.reduce((best, entry) =>
    entry.at > best.at ? entry : best
  );
}

/** Subscribe to health updates (background refresh, successful probes). */
export function subscribeHubHealth(
  listener: (status: ApiHealthStatus) => void
): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getHubHealthCache(): ApiHealthStatus | null {
  const entry = pickBestCache();
  if (!entry) return null;
  if (!isFresh(entry, CACHE_TTL_MS)) return null;
  memoryCache = entry;
  return entry.status;
}

/** Last known good auth — survives navigation and transient offline blips. */
export function getLastKnownGoodHealth(): ApiHealthStatus | null {
  const entry = pickBestCache();
  if (!entry) return null;
  if (!entry.status.online || !entry.status.authenticated) return null;
  if (!isFresh(entry, STALE_OK_TTL_MS)) return null;
  memoryCache = entry;
  return entry.status;
}

function setHubHealthCache(status: ApiHealthStatus): void {
  if (!status.online || !status.authenticated) return;
  const entry: CachedHealth = { at: Date.now(), status };
  memoryCache = entry;
  writeStorageCache(entry);
  notifyListeners(status);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchHealthPath(
  path: string,
  timeoutMs: number
): Promise<Response | null> {
  try {
    return await fetch(hubApiUrl(path), {
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch {
    return null;
  }
}

function parseHealthResponse(res: Response): ApiHealthStatus {
  const offline: ApiHealthStatus = { online: false, authenticated: false };
  if (res.status === 502) return offline;
  if (res.status === 503) return { online: true, authenticated: false };
  if (res.status === 401) return { online: true, authenticated: false };
  if (res.ok) return { online: true, authenticated: true };
  return offline;
}

/** One round-trip via the Next.js proxy — validates backend + Hub key injection. */
export async function probeHubApi(
  timeoutMs = DEFAULT_TIMEOUT_MS
): Promise<ApiHealthStatus> {
  const offline: ApiHealthStatus = { online: false, authenticated: false };
  const statusTimeout = Math.min(timeoutMs, 8_000);
  const healthTimeout = Math.min(4_000, Math.max(2_000, Math.floor(timeoutMs / 4)));

  const statusRes = await fetchHealthPath("/status", statusTimeout);
  if (statusRes) return parseHealthResponse(statusRes);

  // Backend may be busy (coding agent) — /health stays lightweight.
  const healthRes = await fetchHealthPath("/health", healthTimeout);
  if (healthRes?.ok) return { online: true, authenticated: true };

  return offline;
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

  const lastProbe = await probeHubApi();
  if (lastProbe.online && lastProbe.authenticated) {
    setHubHealthCache(lastProbe);
    return lastProbe;
  }

  // Transient offline — keep last known good so bureau navigation doesn't flash errors.
  const staleOk = getLastKnownGoodHealth();
  if (staleOk && !lastProbe.online) {
    return staleOk;
  }

  return lastProbe;
}

/** Background refresh — never blocks UI with a false negative. */
export function refreshHubHealthInBackground(): void {
  void probeHubApi().then((status) => {
    if (status.online && status.authenticated) {
      setHubHealthCache(status);
    }
  });
}

/** Instant read for dashboards — falls back to last known good on transient failures. */
export async function resolveHubHealthFast(): Promise<ApiHealthStatus> {
  const cached = getHubHealthCache() ?? getLastKnownGoodHealth();
  if (cached) return cached;

  const probed = await probeHubApi(8_000);
  if (probed.online && probed.authenticated) {
    setHubHealthCache(probed);
    return probed;
  }

  const staleOk = getLastKnownGoodHealth();
  if (staleOk) return staleOk;

  return probed;
}
