import { hubFetch } from "@/lib/hub-fetch";
import type { BureauKey } from "@/lib/agent-bureau";

export type LibraryTiming = "now" | "later";

export interface LibraryEntry {
  id: string;
  bureau: string;
  title: string;
  summary: string;
  timing: LibraryTiming;
  source_url?: string;
  source_title?: string;
  topics: string[];
  agent_id?: string;
  requested_by?: string;
  query?: string;
  created_at: string;
}

export interface LibraryBureauMeta {
  id: string;
  label: string;
  entry_count: number;
}

export interface LibraryListResponse {
  entries: LibraryEntry[];
  total: number;
  counts_by_bureau: Record<string, number>;
  counts_by_timing: { now: number; later: number };
}

export interface LibraryResearchResult {
  success: boolean;
  query?: string;
  message?: string;
  status?: string;
  entries_saved?: number;
  entries?: LibraryEntry[];
}

export interface LibraryCeoReport {
  generated_at: string;
  entry_count: number;
  hub_suggestions: string[];
  rnd_ideas: string[];
  useful_now: string[];
  kept_for_later: string[];
  executive_summary?: string;
  markdown: string;
}

export async function fetchLibraryBureaus(): Promise<{ bureaus: LibraryBureauMeta[] }> {
  return hubFetch("/library/bureaus");
}

export async function fetchLibraryEntries(params?: {
  bureau?: BureauKey | string;
  timing?: LibraryTiming;
  limit?: number;
}): Promise<LibraryListResponse> {
  const q = new URLSearchParams();
  if (params?.bureau) q.set("bureau", params.bureau);
  if (params?.timing) q.set("timing", params.timing);
  if (params?.limit) q.set("limit", String(params.limit));
  const suffix = q.toString() ? `?${q}` : "";
  return hubFetch(`/library/entries${suffix}`);
}

export interface LibraryTopic {
  slug: string;
  label: string;
  titles?: string[];
  bureaus?: string[];
  has_now?: boolean;
  learn_count?: number;
  entry_ids?: string[];
}

export interface LibraryTopicsResponse {
  topics: LibraryTopic[];
  total: number;
  offset: number;
  limit: number;
  updated_at?: string;
}

/** Topic catalog (not the raw entries list above) — used by MemberDetailPanel's
 * "Mémoire" tab to show what an agent's bureau has actually learned. */
export async function fetchLibraryTopics(params?: {
  bureau?: BureauKey | string;
  limit?: number;
}): Promise<LibraryTopicsResponse> {
  const q = new URLSearchParams();
  if (params?.bureau) q.set("bureau", params.bureau);
  if (params?.limit) q.set("limit", String(params.limit));
  const suffix = q.toString() ? `?${q}` : "";
  return hubFetch(`/library/topics${suffix}`);
}

export async function runLibraryResearch(
  query: string,
  options?: { bureaus?: string[]; wait?: boolean }
): Promise<LibraryResearchResult> {
  const wait = options?.wait ?? false;
  return hubFetch<LibraryResearchResult>("/library/research", {
    method: "POST",
    body: JSON.stringify({
      query,
      bureaus: options?.bureaus,
      requested_by: "ceo",
      wait,
    }),
    timeoutMs: wait ? 300_000 : 30_000,
  });
}

export async function fetchLibraryCeoReport(days = 7): Promise<LibraryCeoReport> {
  return hubFetch<LibraryCeoReport>("/library/report", {
    method: "POST",
    body: JSON.stringify({ days }),
    timeoutMs: 90_000,
  });
}

export interface LibraryEnrichResult {
  success: boolean;
  entries_processed: number;
  agents_enriched: number;
  agents: string[];
  message: string;
  status?: {
    library_entries: number;
    library_now: number;
    agents_with_memories: number;
    agents_total: number;
  };
}

export async function enrichTeamFromLibrary(options?: {
  days?: number;
  timing?: LibraryTiming;
  limit?: number;
}): Promise<LibraryEnrichResult> {
  return hubFetch<LibraryEnrichResult>("/library/enrich", {
    method: "POST",
    body: JSON.stringify({
      days: options?.days ?? 30,
      timing: options?.timing,
      limit: options?.limit ?? 25,
    }),
    timeoutMs: 120_000,
  });
}

function normalizeDistributionStatus(
  data: Record<string, unknown>,
): LibraryDistributionStatus {
  const totalEntries = Number(data.total_entries ?? data.library_entries ?? 0);
  const totalSlots = Number(data.total_slots ?? 0);
  const distributed = Number(data.distributed_slots ?? 0);
  const learned = Number(data.learned_slots ?? data.agents_with_memories ?? 0);
  const pct = (n: number, d: number) => (d > 0 ? Math.round((n / d) * 1000) / 10 : 0);

  return {
    total_entries: totalEntries,
    total_slots: totalSlots,
    distributed_slots: distributed,
    learned_slots: learned,
    verified_slots: Number(data.verified_slots ?? 0),
    mem0_confirmed_slots: Number(data.mem0_confirmed_slots ?? 0),
    entries_fully_distributed: Number(data.entries_fully_distributed ?? 0),
    entries_fully_learned: Number(data.entries_fully_learned ?? 0),
    entries_fully_verified: Number(data.entries_fully_verified ?? 0),
    entries_pending_distribution: Number(
      data.entries_pending_distribution ?? totalEntries,
    ),
    distribution_pct: Number(data.distribution_pct ?? pct(distributed, totalSlots)),
    learned_pct: Number(data.learned_pct ?? pct(learned, totalSlots)),
    verified_pct: Number(data.verified_pct ?? 0),
    agents_total: Number(data.agents_total ?? 0),
    bureaus: Number(data.bureaus ?? 0),
    by_bureau: (data.by_bureau as LibraryDistributionStatus["by_bureau"]) ?? {},
    active_job: (data.active_job as LibraryDistributionStatus["active_job"]) ?? null,
    ledger_receipts: Number(data.ledger_receipts ?? 0),
  };
}

export async function fetchLibraryEnrichStatus(): Promise<LibraryDistributionStatus> {
  const paths = ["/library/enrich/status", "/library/distribution/status"];
  let lastError: Error | null = null;
  for (const path of paths) {
    try {
      const data = await hubFetch<Record<string, unknown>>(path);
      return normalizeDistributionStatus(data);
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      if (!lastError.message.toLowerCase().includes("introuvable")) {
        throw lastError;
      }
    }
  }
  throw lastError ?? new Error("Statut bibliothèque indisponible");
}

export interface LibraryDistributionStatus {
  total_entries: number;
  total_slots: number;
  distributed_slots: number;
  learned_slots: number;
  verified_slots: number;
  mem0_confirmed_slots: number;
  entries_fully_distributed: number;
  entries_fully_learned: number;
  entries_fully_verified: number;
  entries_pending_distribution: number;
  distribution_pct: number;
  learned_pct: number;
  verified_pct: number;
  agents_total: number;
  bureaus: number;
  by_bureau: Record<
    string,
    {
      entries: number;
      slots: number;
      distributed: number;
      learned: number;
      verified: number;
    }
  >;
  active_job: LibraryDistributionJob | null;
  ledger_receipts: number;
}

export interface LibraryDistributionJob {
  id: string;
  kind: string;
  status: "queued" | "running" | "completed" | "failed";
  processed: number;
  total: number;
  distributed: number;
  learned: number;
  verified: number;
  errors: number;
  message: string;
  started_at?: string;
  finished_at?: string | null;
}

export interface LibraryJobResponse {
  success: boolean;
  job_id?: string;
  status?: LibraryDistributionJob;
  message: string;
}

async function postLibraryJob(
  paths: string[],
  body?: Record<string, unknown>,
): Promise<LibraryJobResponse> {
  let lastError: Error | null = null;
  for (const path of paths) {
    try {
      return await hubFetch<LibraryJobResponse>(path, {
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
        timeoutMs: 30_000,
      });
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      if (!lastError.message.toLowerCase().includes("introuvable")) {
        throw lastError;
      }
    }
  }
  throw lastError ?? new Error("Action bibliothèque indisponible");
}

export async function distributeAllLibrary(options?: {
  skip_distributed?: boolean;
  timing?: LibraryTiming;
  run_learning?: boolean;
}): Promise<LibraryJobResponse> {
  return postLibraryJob(
    ["/library/enrich/distribute-all", "/library/distribution/distribute-all"],
    {
      skip_distributed: options?.skip_distributed ?? true,
      timing: options?.timing,
      run_learning: options?.run_learning ?? false,
    },
  );
}

export async function learnPendingLibrary(): Promise<LibraryJobResponse> {
  return postLibraryJob([
    "/library/enrich/learn-pending",
    "/library/distribution/learn-pending",
  ]);
}

export async function verifyLibraryMem0(): Promise<LibraryJobResponse> {
  return postLibraryJob([
    "/library/enrich/verify",
    "/library/distribution/verify",
  ]);
}

export async function fetchLibraryDistributionJob(
  jobId: string,
): Promise<LibraryDistributionJob> {
  return hubFetch(`/library/distribution/jobs/${encodeURIComponent(jobId)}`);
}

export interface LibraryRetentionPreview {
  policy: Record<string, unknown>;
  total_entries: number;
  compress_candidates: number;
  purge_candidates: number;
  archives_count: number;
  message: string;
}

export async function fetchLibraryRetentionPreview(): Promise<LibraryRetentionPreview> {
  return hubFetch("/library/retention/preview");
}

export async function applyLibraryRetention(options?: {
  compress?: boolean;
  purge?: boolean;
  dry_run?: boolean;
}): Promise<Record<string, unknown>> {
  return hubFetch("/library/retention/apply", {
    method: "POST",
    body: JSON.stringify({
      compress: options?.compress ?? true,
      purge: options?.purge ?? true,
      dry_run: options?.dry_run ?? false,
    }),
    timeoutMs: 120_000,
  });
}

export async function cancelLibraryJob(): Promise<{ success: boolean; message: string }> {
  return postLibraryJob(["/library/jobs/cancel", "/library/enrich/jobs/cancel"]);
}

/** @deprecated use fetchLibraryEnrichStatus */
export async function fetchLibraryEnrichStatusLegacy(): Promise<{
  library_entries: number;
  library_now: number;
  agents_with_memories: number;
  agents_total: number;
}> {
  return hubFetch("/library/enrich/status");
}
