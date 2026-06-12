/** Shared X-Hub-Key header for authenticated Hub API calls. */
export function hubApiKeyHeaders(
  extra?: HeadersInit
): Record<string, string> {
  const headers: Record<string, string> = {};
  const key = process.env.NEXT_PUBLIC_HUB_API_KEY;
  if (key) {
    headers["X-Hub-Key"] = key;
  }

  if (!extra) {
    return headers;
  }

  if (extra instanceof Headers) {
    extra.forEach((value, name) => {
      headers[name] = value;
    });
    return headers;
  }

  if (Array.isArray(extra)) {
    for (const [name, value] of extra) {
      headers[name] = value;
    }
    return headers;
  }

  return { ...headers, ...extra };
}
