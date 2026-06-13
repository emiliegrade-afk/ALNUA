import { hubApiUrl } from "./hub-api-config";
import { hubFetch } from "./hub-fetch";

export type BetaFeedbackType = "bug" | "suggestion" | "crash" | "ux" | "autre";
export type BetaSeverity = "bloquant" | "majeur" | "mineur" | "cosmétique";

export interface BetaProjectInfo {
  project_id: string;
  project_name: string;
  project_slug: string;
  app_version: string | null;
  test_instructions: string;
  status: string;
}

export interface BetaTester {
  id: string;
  project_id: string;
  project_name?: string;
  email: string;
  first_name: string | null;
  device: string | null;
  os_version: string | null;
  app_version: string | null;
  joined_at: string;
  feedback_count: number;
}

export interface BetaFeedback {
  id: string;
  tester_id: string;
  project_id: string;
  project_name?: string;
  tester_name?: string | null;
  tester_email?: string | null;
  type: BetaFeedbackType | null;
  title: string;
  description: string | null;
  screenshot_url: string | null;
  severity: BetaSeverity | null;
  ticket_id: string | null;
  created_at: string;
}

export interface BetaStats {
  total_testers: number;
  total_feedback: number;
  feedback_this_week: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  timeline_7d: { date: string; count: number }[];
}

export interface BetaRegisterResult {
  tester_id: string;
  token: string;
  first_name: string | null;
  project_name: string;
  app_version: string | null;
}

export interface BetaFeedbackResult {
  feedback_id: string;
  ticket_id: string;
}

async function betaFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  return hubFetch<T>(path, options);
}

export function betaStorageKey(projectSlug: string) {
  return `beta_token_${projectSlug}`;
}

export function betaProfileKey(projectSlug: string) {
  return `beta_profile_${projectSlug}`;
}

export interface BetaStoredProfile {
  first_name: string;
  project_name: string;
  app_version: string | null;
}

export async function fetchBetaInfo(projectSlug: string): Promise<BetaProjectInfo> {
  return betaFetch<BetaProjectInfo>(`/beta/info/${encodeURIComponent(projectSlug)}`);
}

export async function registerBetaTester(body: {
  project_slug: string;
  email: string;
  first_name: string;
  device?: string;
  os_version?: string;
  app_version?: string;
}): Promise<BetaRegisterResult> {
  return betaFetch<BetaRegisterResult>("/beta/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function submitBetaFeedback(
  token: string,
  body: {
    project_slug: string;
    type: BetaFeedbackType;
    title: string;
    description: string;
    severity?: BetaSeverity;
    screenshot_base64?: string;
  }
): Promise<BetaFeedbackResult> {
  return betaFetch<BetaFeedbackResult>("/beta/feedback", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
}

export async function fetchMyBetaFeedback(token: string): Promise<BetaFeedback[]> {
  return betaFetch<BetaFeedback[]>("/beta/my-feedback", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function fetchBetaTesters(projectId?: string): Promise<BetaTester[]> {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return betaFetch<BetaTester[]>(`/beta/testers${qs}`);
}

export async function fetchBetaFeedbackList(params?: {
  project_id?: string;
  tester_id?: string;
}): Promise<BetaFeedback[]> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.tester_id) qs.set("tester_id", params.tester_id);
  const query = qs.toString();
  return betaFetch<BetaFeedback[]>(`/beta/feedback${query ? `?${query}` : ""}`);
}

export async function fetchBetaStats(projectId?: string): Promise<BetaStats> {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return betaFetch<BetaStats>(`/beta/stats${qs}`);
}

export async function createBetaInvite(projectId: string): Promise<{
  invite_url: string;
  project_slug: string;
}> {
  return betaFetch("/beta/invite", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });
}

export function betaTestersCsvUrl(projectId?: string): string {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return hubApiUrl(`/beta/testers/export${qs}`);
}
