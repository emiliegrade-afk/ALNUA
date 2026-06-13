/** Browser calls go through /api/hub — the key is injected server-side. */
export function isHubApiKeyConfigured(): boolean {
  if (typeof window !== "undefined") {
    return true;
  }
  return Boolean(process.env.HUB_API_KEY?.trim());
}

function mergeHeaders(
  base: Record<string, string>,
  extra?: HeadersInit
): Record<string, string> {
  if (!extra) {
    return base;
  }

  if (extra instanceof Headers) {
    extra.forEach((value, name) => {
      base[name] = value;
    });
    return base;
  }

  if (Array.isArray(extra)) {
    for (const [name, value] of extra) {
      base[name] = value;
    }
    return base;
  }

  return { ...base, ...extra };
}

/** Attach X-Hub-Key only for direct backend calls (SSR). Browser uses the proxy. */
export function hubApiKeyHeaders(
  extra?: HeadersInit
): Record<string, string> {
  const headers: Record<string, string> = {};

  if (typeof window === "undefined") {
    const key = process.env.HUB_API_KEY?.trim();
    if (key) {
      headers["X-Hub-Key"] = key;
    }
  }

  return mergeHeaders(headers, extra);
}
