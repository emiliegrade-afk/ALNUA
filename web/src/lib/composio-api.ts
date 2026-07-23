import { hubFetch } from "./hub-fetch";

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
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  return hubFetch<T>(path, options);
}

export async function fetchComposioApps(
  userId = "alnua_coo"
): Promise<ComposioApp[]> {
  const data = await composioFetch<ComposioApp[] | { apps?: ComposioApp[] }>(
    `/composio/apps?user_id=${encodeURIComponent(userId)}`,
    { timeoutMs: 60_000 },
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
