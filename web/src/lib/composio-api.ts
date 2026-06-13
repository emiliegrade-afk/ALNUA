import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";

export interface ComposioApp {
  app: string;
  status?: string;
  connected?: boolean;
}

export interface ComposioConnectResponse {
  app: string;
  oauth_url: string;
}

async function composioFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(hubApiUrl(path), {
    ...options,
    headers: hubApiKeyHeaders({
      "Content-Type": "application/json",
      ...options?.headers,
    }),
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }

  return res.json() as Promise<T>;
}

export async function fetchComposioApps(
  userId = "alnua_coo"
): Promise<ComposioApp[]> {
  const data = await composioFetch<ComposioApp[] | { apps?: ComposioApp[] }>(
    `/composio/apps?user_id=${encodeURIComponent(userId)}`
  );
  if (Array.isArray(data)) return data;
  return data.apps ?? [];
}

export async function connectComposioApp(
  appName: string,
  userId = "alnua_coo"
): Promise<ComposioConnectResponse> {
  return composioFetch<ComposioConnectResponse>(
    `/composio/connect/${encodeURIComponent(appName)}?user_id=${encodeURIComponent(userId)}`,
    { method: "POST" }
  );
}
