import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";
import { parseHubApiError } from "./hub-api-error";

export async function hubFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  const { timeoutMs = 30_000, ...fetchOptions } = options ?? {};
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const isFormData = fetchOptions.body instanceof FormData;

  try {
    const res = await fetch(hubApiUrl(path), {
      ...fetchOptions,
      signal: controller.signal,
      headers: hubApiKeyHeaders(
        isFormData
          ? fetchOptions.headers
          : {
              "Content-Type": "application/json",
              ...fetchOptions.headers,
            }
      ),
      cache: "no-store",
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(parseHubApiError(text, res.status));
    }

    if (res.status === 204) {
      return undefined as T;
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
