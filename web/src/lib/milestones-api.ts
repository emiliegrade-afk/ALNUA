import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";
import { parseHubApiError } from "./hub-api-error";

export interface Milestone {
  id: string;
  title: string;
  date: string;
  pole: string;
  description: string;
  validated: boolean;
  validated_at: string | null;
}

async function milestonesFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(hubApiUrl(path), {
    ...init,
    headers: {
      ...hubApiKeyHeaders(),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(parseHubApiError(text, res.status));
  }
  return res.json() as Promise<T>;
}

export async function fetchMilestones(daysAhead = 120): Promise<Milestone[]> {
  const data = await milestonesFetch<{ milestones: Milestone[] }>(
    `/agents/secretary/milestones?days_ahead=${daysAhead}`,
  );
  return data.milestones;
}

export async function createMilestone(
  title: string,
  dateIso: string,
  pole: string,
  description = "",
): Promise<{ success: boolean; id?: string; error?: string }> {
  return milestonesFetch("/agents/secretary/milestones", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, date_iso: dateIso, pole, description }),
  });
}

export async function updateMilestone(
  eventId: string,
  fields: { title?: string; date_iso: string; pole?: string; description?: string },
): Promise<{ success: boolean; error?: string }> {
  return milestonesFetch(`/agents/secretary/milestones/${encodeURIComponent(eventId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
}

export async function validateMilestone(
  eventId: string,
  validated = true,
): Promise<{ success: boolean; id: string; validated: boolean }> {
  return milestonesFetch(`/agents/secretary/milestones/${encodeURIComponent(eventId)}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ validated }),
  });
}
