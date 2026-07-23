import { hubApiUrl } from "./hub-api-config";

export interface SavCase {
  id: string;
  product_slug: string;
  channel: string;
  customer_ref?: string | null;
  subject: string;
  body: string;
  category: string;
  status: string;
  draft_reply?: string | null;
  needs_ceo: boolean;
  confidence: number;
  created_at?: string | null;
}

export interface ProductKb {
  slug: string;
  name: string;
  support_email: string;
  faq_md: string;
  auto_reply_ok: boolean;
  tone: string;
}

async function savFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(hubApiUrl(path), {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `SAV API ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function fetchSavCases(params?: {
  product_slug?: string;
  status?: string;
  needs_ceo?: boolean;
}): Promise<{ cases: SavCase[] }> {
  const q = new URLSearchParams();
  if (params?.product_slug) q.set("product_slug", params.product_slug);
  if (params?.status) q.set("status", params.status);
  if (params?.needs_ceo !== undefined) q.set("needs_ceo", String(params.needs_ceo));
  const suffix = q.toString() ? `?${q}` : "";
  return savFetch(`/sav/cases${suffix}`);
}

export function fetchSavKb(): Promise<{ items: ProductKb[] }> {
  return savFetch("/sav/kb");
}

export function createSavCase(payload: {
  product_slug: string;
  subject: string;
  body: string;
  channel?: string;
}): Promise<{
  success: boolean;
  case_id?: string;
  status?: string;
  needs_ceo?: boolean;
  draft_reply?: string;
  error?: string;
}> {
  return savFetch("/sav/cases", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function approveSavCase(
  caseId: string,
  finalReply?: string
): Promise<{ success: boolean; status?: string; draft_reply?: string }> {
  return savFetch(`/sav/cases/${caseId}/approve`, {
    method: "POST",
    body: JSON.stringify({ final_reply: finalReply ?? null }),
  });
}

export function syncSavKb(): Promise<{ synced: number }> {
  return savFetch("/sav/kb/sync", { method: "POST" });
}

export function runSavWorkflow(): Promise<{
  success: boolean;
  summary: string;
  status: string;
}> {
  return savFetch("/sav/workflow/run", { method: "POST" });
}
