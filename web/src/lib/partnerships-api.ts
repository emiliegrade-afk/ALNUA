import { hubApiBase, hubBackendBaseUrl } from "./hub-api-config";
import { hubFetch } from "./hub-fetch";

function resolveAffiliateBase(): string {
  const configured = process.env.NEXT_PUBLIC_AFFILIATE_BASE_URL?.replace(/\/$/, "");
  if (configured) return configured;
  if (typeof window !== "undefined") {
    return `${window.location.origin}/api/hub`;
  }
  return hubBackendBaseUrl() || hubApiBase();
}

const AFFILIATE_BASE = resolveAffiliateBase();

export type PartnerType =
  | "influencer"
  | "creator"
  | "brand"
  | "affiliate"
  | "investor"
  | "distributor"
  | "press";

export type PartnerStatus =
  | "prospect"
  | "contacted"
  | "in_discussion"
  | "agreement"
  | "active"
  | "paused"
  | "declined";

export type PartnerDirection = "outbound" | "inbound";

export interface Partner {
  id: string;
  type: PartnerType | string;
  status: PartnerStatus | string;
  direction: PartnerDirection;
  name: string;
  company: string | null;
  email: string | null;
  instagram_url: string | null;
  tiktok_url: string | null;
  youtube_url: string | null;
  website: string | null;
  audience_size: number | null;
  audience_description: string | null;
  project_ids: string[];
  notes: string | null;
  contract_path: string | null;
  next_followup: string | null;
  last_contact_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface PartnerInteraction {
  id: string;
  partner_id: string;
  date: string;
  type: string | null;
  note: string | null;
  created_at: string;
}

export interface AffiliateLink {
  id: string;
  partner_id: string;
  project_id: string | null;
  code: string;
  redirect_url: string;
  commission_type: string | null;
  commission_value: number | null;
  clicks: number;
  conversions: number;
  revenue_generated: number;
  active: boolean;
  created_at: string;
  public_url?: string;
  partner_name?: string;
}

export interface PartnershipRequest {
  id: string;
  name: string;
  email: string;
  type: string | null;
  message: string | null;
  instagram_url: string | null;
  tiktok_url: string | null;
  website: string | null;
  audience_size: string | null;
  project_interest: string | null;
  status: string;
  partner_id: string | null;
  created_at: string;
}

export interface PartnershipStats {
  total_active: number;
  total_prospects: number;
  top_affiliates: AffiliateLink[];
  requests_this_week: number;
  followups_due_today: number;
  new_requests: number;
}

export interface AffiliateTimelinePoint {
  date: string;
  clicks: number;
  conversions: number;
}

export function affiliateGoUrl(code: string): string {
  return `${AFFILIATE_BASE}/go/${code}`;
}

export async function fetchPartners(params?: {
  type?: string;
  status?: string;
  direction?: string;
  project_id?: string;
}): Promise<Partner[]> {
  const qs = new URLSearchParams();
  if (params?.type) qs.set("type", params.type);
  if (params?.status) qs.set("status", params.status);
  if (params?.direction) qs.set("direction", params.direction);
  if (params?.project_id) qs.set("project_id", params.project_id);
  const q = qs.toString();
  return hubFetch<Partner[]>(`/partners${q ? `?${q}` : ""}`);
}

export async function fetchPartnershipStats(): Promise<PartnershipStats> {
  return hubFetch<PartnershipStats>("/partners/stats");
}

export async function createPartner(
  body: Partial<Partner> & { name: string; type: string; direction: PartnerDirection }
): Promise<Partner> {
  return hubFetch<Partner>("/partners", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updatePartner(
  id: string,
  body: Partial<Partner>
): Promise<Partner> {
  return hubFetch<Partner>(`/partners/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deletePartner(id: string): Promise<void> {
  await hubFetch(`/partners/${id}`, { method: "DELETE" });
}

export async function fetchPartnerInteractions(
  partnerId: string
): Promise<PartnerInteraction[]> {
  return hubFetch<PartnerInteraction[]>(`/partners/${partnerId}/interactions`);
}

export async function createPartnerInteraction(
  partnerId: string,
  body: { type?: string; note?: string }
): Promise<PartnerInteraction> {
  return hubFetch<PartnerInteraction>(`/partners/${partnerId}/interactions`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function uploadPartnerContract(
  partnerId: string,
  file: File
): Promise<Partner> {
  const form = new FormData();
  form.append("file", file);
  return hubFetch<Partner>(`/partners/${partnerId}/contract`, {
    method: "POST",
    body: form,
  });
}

export async function openPartnerContract(partnerId: string): Promise<void> {
  await hubFetch(`/partners/${partnerId}/contract/open`, { method: "GET" });
}

export async function openContractsFolder(): Promise<void> {
  await hubFetch("/partners/contracts/open-folder", { method: "POST" });
}

export async function fetchAffiliateLinks(
  partnerId?: string
): Promise<AffiliateLink[]> {
  const q = partnerId ? `?partner_id=${partnerId}` : "";
  return hubFetch<AffiliateLink[]>(`/affiliate-links${q}`);
}

export async function createAffiliateLink(body: {
  partner_id: string;
  project_id?: string;
  code?: string;
  redirect_url: string;
  commission_type?: string;
  commission_value?: number;
}): Promise<AffiliateLink> {
  return hubFetch<AffiliateLink>("/affiliate-links", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchAffiliateTimeline(
  linkId: string,
  days = 30
): Promise<AffiliateTimelinePoint[]> {
  return hubFetch<AffiliateTimelinePoint[]>(
    `/affiliate-links/${linkId}/timeline?days=${days}`
  );
}

export async function submitPartnershipRequest(body: {
  name: string;
  email: string;
  type?: string;
  message?: string;
  instagram_url?: string;
  tiktok_url?: string;
  website?: string;
  audience_size?: string;
  project_interest?: string;
}): Promise<PartnershipRequest> {
  return hubFetch<PartnershipRequest>("/partnerships/request", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchPartnershipRequests(
  status?: string
): Promise<PartnershipRequest[]> {
  const q = status ? `?status=${status}` : "";
  return hubFetch<PartnershipRequest[]>(`/partnerships/requests${q}`);
}

export async function updatePartnershipRequest(
  id: string,
  body: { status: string }
): Promise<PartnershipRequest> {
  return hubFetch<PartnershipRequest>(`/partnerships/requests/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function convertPartnershipRequest(id: string): Promise<{
  partner: Partner;
  request_id: string;
}> {
  return hubFetch(`/partnerships/requests/${id}/convert`, { method: "POST" });
}
