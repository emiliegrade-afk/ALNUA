import { hubFetch } from "./hub-fetch";

export interface Ue58Status {
  ok: boolean;
  configured: boolean;
  connected: boolean;
  bridge?: string;
  protocol_version?: string;
  base_url?: string | null;
  error?: string;
  server?: Record<string, unknown>;
}

export function fetchUe58Status(): Promise<Ue58Status> {
  return hubFetch<Ue58Status>("/gaming/ue58/status");
}

export function ue58Chat(body: {
  agent_id: string;
  message: string;
  session_id?: string;
}): Promise<Record<string, unknown>> {
  return hubFetch("/gaming/ue58/chat", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 60_000,
  });
}

export interface StudioAgencyStatus {
  ok: boolean;
  configured: boolean;
  project_path?: string | null;
  error?: string | null;
  claude_code_cli?: boolean;
  coding_backend?: string;
  ue58?: { configured?: boolean; connected?: boolean; error?: string };
  mode?: Record<string, string>;
}

export function fetchStudioAgencyStatus(): Promise<StudioAgencyStatus> {
  return hubFetch<StudioAgencyStatus>("/gaming/studio/agency/status");
}

export function runStudioAgency(body: {
  agent_id: string;
  title: string;
  description: string;
}): Promise<Record<string, unknown>> {
  return hubFetch("/gaming/studio/agency/run", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 3_600_000,
  });
}
