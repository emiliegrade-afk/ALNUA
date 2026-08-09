import { hubPublicApiUrl } from "./hub-api-config";
import { hubFetch } from "./hub-fetch";
import { fetchRndIdea } from "./rnd";

export type DossierStatus =
  | "draft"
  | "committee_active"
  | "partial_validated"
  | "ready_for_ceo"
  | "ceo_approved"
  | "ceo_rejected"
  | "in_conception"
  | "published"
  | "archived";

export type SectionStatus =
  | "draft"
  | "under_review"
  | "validated"
  | "needs_revision"
  | "skipped";

export interface RndDossierSection {
  id: string;
  dossier_id: string;
  section_key: string;
  title: string;
  content_md: string;
  status: SectionStatus;
  sort_order: number;
  validated_by?: string | null;
  validated_at?: string | null;
  revision_note?: string | null;
}

export interface RndDossierListItem {
  id: string;
  slug: string;
  title: string;
  domain: string;
  branch?: string | null;
  status: DossierStatus;
  ceo_status: string;
  idea_legacy_id?: string | null;
  sections_validated_count: number;
  sections_total_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface RndFinanceJson {
  finance_version?: number;
  cost_model?: string;
  capex_eur?: number;
  capex_dev_eur?: number;
  capex_llm_agents_eur?: number;
  capex_dossier_llm_eur?: number;
  capex_marketing_eur?: number;
  opex_monthly_eur?: number;
  opex_incremental_eur?: number;
  opex_existing_alnua_eur?: number;
  llm_monthly_eur?: number;
  dev_weeks?: number;
  dev_hours?: number;
  break_even_months?: number | null;
  runway_impact_months?: number;
  treasury_ytd_eur?: number;
  monthly_balance_eur?: number;
  portfolio_monthly_revenue_eur?: number;
  portfolio_apps_count?: number;
  portfolio_app_names?: string[];
  net_impact_6m_eur?: number;
  net_impact_12m_eur?: number;
  verdict_finance?: string;
  assumptions?: string[];
  funding_options?: string[];
  reasoning?: string;
  revenue_hypothesis?: {
    pricing_model?: {
      model_type?: string;
      currency?: string;
      blended_arpu_eur?: number;
      source?: string;
      promo_note?: string;
      price_range_eur?: { min?: number; max?: number };
      tiers?: Array<{
        name: string;
        price_eur: number;
        mix_pct?: number;
        billing?: string;
      }>;
    };
    paying_subscribers?: { m3?: number; m6?: number; m12?: number };
    blended_arpu_eur?: number;
    m3_monthly_run_rate_eur?: number;
    portfolio_baseline_monthly_eur?: number;
    per_app_baseline_monthly_eur?: number;
    active_apps_count?: number;
    m6_monthly_run_rate_eur?: number;
    m12_monthly_run_rate_eur?: number;
    cumulative_6m_eur?: number;
    cumulative_12m_eur?: number;
    conservative_m6_monthly_eur?: number;
    conservative_m12_monthly_eur?: number;
    optimistic_m6_monthly_eur?: number;
    optimistic_m12_monthly_eur?: number;
    conservative_cumulative_12m_eur?: number;
    optimistic_cumulative_12m_eur?: number;
    pricing_eur?: number;
    conversion_rate?: number;
    users_m6?: number;
    users_m12?: number;
    revenue_m6_eur?: number;
    revenue_m12_eur?: number;
  };
  accountant_commentary?: string;
}

export interface RndDossierDetail extends RndDossierListItem {
  idea_id: string;
  tagline?: string | null;
  branch?: string | null;
  ceo_note?: string | null;
  committee_team: Record<string, unknown>[];
  vision_snapshot?: string | null;
  competitive_context?: string | null;
  finance_json?: RndFinanceJson | null;
  deck_html_path?: string | null;
  deck_pdf_path?: string | null;
  one_pager_md?: string | null;
  ceo_package_json?: Record<string, unknown> | null;
  committee_report_md?: string | null;
  dispatch_json?: Record<string, unknown> | null;
  dispatch_status?: string;
  local_path?: string | null;
  sections: RndDossierSection[];
}

export interface RndDeckGenerateResult {
  dossier_id: string;
  html_path?: string | null;
  pdf_path?: string | null;
  html_url?: string | null;
  pdf_url?: string | null;
  slide_count: number;
  pdf_error?: string | null;
  message: string;
}

export interface RndDossierEvent {
  id: string;
  dossier_id: string;
  event_type: string;
  actor: string;
  payload?: Record<string, unknown> | null;
  created_at: string;
}

export interface PromoteResponse {
  dossier: RndDossierDetail;
  idea: Record<string, unknown>;
  message: string;
  enriching?: boolean;
}

export async function createRndDossier(
  ideaId: string,
  options?: { enrich?: boolean }
): Promise<PromoteResponse> {
  const qs = options?.enrich === false ? "?enrich=false" : "";
  return hubFetch<PromoteResponse>(`/rnd/dossiers${qs}`, {
    method: "POST",
    body: JSON.stringify({ idea_id: ideaId }),
  });
}

export async function fetchRndDossiers(params?: {
  status?: string;
  domain?: string;
}): Promise<RndDossierListItem[]> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.domain) qs.set("domain", params.domain);
  const q = qs.toString();
  return hubFetch<RndDossierListItem[]>(`/rnd/dossiers${q ? `?${q}` : ""}`);
}

export async function fetchRndDossier(dossierIdOrSlug: string): Promise<RndDossierDetail> {
  const ref = dossierIdOrSlug.trim();
  const errors: string[] = [];

  async function tryFetch(path: string): Promise<RndDossierDetail | null> {
    try {
      return await hubFetch<RndDossierDetail>(path, { timeoutMs: 90_000 });
    } catch (e) {
      errors.push(e instanceof Error ? e.message : String(e));
      return null;
    }
  }

  const byId = await tryFetch(`/rnd/dossiers/${encodeURIComponent(ref)}`);
  if (byId) return byId;

  const bySlug = await tryFetch(`/rnd/dossiers/slug/${encodeURIComponent(ref)}`);
  if (bySlug) return bySlug;

  // Legacy idea id (idea_xxx) → resolve via rnd_ideas.dossier_id
  if (ref.startsWith("idea_")) {
    try {
      const idea = await fetchRndIdea(ref);
      if (idea.dossier_id) {
        const linked = await tryFetch(
          `/rnd/dossiers/${encodeURIComponent(idea.dossier_id)}`
        );
        if (linked) return linked;
      }
    } catch (e) {
      errors.push(e instanceof Error ? e.message : String(e));
    }
  }

  throw new Error(
    errors.find((m) => m.includes("introuvable")) ??
      errors[0] ??
      "Dossier introuvable"
  );
}

export async function fetchRndDossierBySlug(slug: string): Promise<RndDossierDetail> {
  return hubFetch<RndDossierDetail>(`/rnd/dossiers/slug/${slug}`);
}

export async function promoteRndIdea(ideaId: string): Promise<PromoteResponse> {
  return hubFetch<PromoteResponse>(`/rnd/ideas/${encodeURIComponent(ideaId)}/promote`, {
    method: "POST",
  });
}

export async function fetchRndDossierEvents(dossierId: string): Promise<RndDossierEvent[]> {
  return hubFetch<RndDossierEvent[]>(`/rnd/dossiers/${dossierId}/events`);
}

export async function enrichRndDossier(dossierId: string): Promise<RndDossierDetail> {
  const data = await hubFetch<{ dossier: RndDossierDetail }>(
    `/rnd/dossiers/${dossierId}/enrich`,
    { method: "POST" }
  );
  return data.dossier;
}

export async function validateDossierSection(
  dossierId: string,
  sectionKey: string,
  note?: string
): Promise<RndDossierDetail> {
  return hubFetch<RndDossierDetail>(`/rnd/dossiers/${dossierId}/validate-section`, {
    method: "POST",
    body: JSON.stringify({ section_key: sectionKey, note }),
  });
}

export async function requestSectionRevision(
  dossierId: string,
  sectionKey: string,
  revisionNote: string
): Promise<RndDossierDetail> {
  return hubFetch<RndDossierDetail>(`/rnd/dossiers/${dossierId}/request-revision`, {
    method: "POST",
    body: JSON.stringify({ section_key: sectionKey, revision_note: revisionNote }),
  });
}

export async function regenerateDossierSection(
  dossierId: string,
  sectionKey: string,
  body: { revision_note: string }
): Promise<RndDossierDetail> {
  return hubFetch<RndDossierDetail>(`/rnd/dossiers/${dossierId}/regenerate-section`, {
    method: "POST",
    body: JSON.stringify({ section_key: sectionKey, revision_note: body.revision_note }),
  });
}

export async function estimateDossierFinance(
  dossierId: string,
  body?: { constraint?: string }
): Promise<{ finance_json: RndFinanceJson; business_case_md: string }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/finance/estimate`, {
    method: "POST",
    body: JSON.stringify(body ?? {}),
  });
}

export async function fetchDossierFinance(dossierId: string): Promise<{
  finance_json: RndFinanceJson | null;
  business_case: string | null;
}> {
  return hubFetch(`/rnd/dossiers/${dossierId}/finance`);
}

export async function patchRndDossier(
  dossierId: string,
  body: Partial<{
    title: string;
    tagline: string;
    status: DossierStatus;
    ceo_status: string;
    ceo_note: string;
  }>
): Promise<RndDossierDetail> {
  return hubFetch<RndDossierDetail>(`/rnd/dossiers/${dossierId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function updateDossierSection(
  dossierId: string,
  sectionKey: string,
  contentMd: string
): Promise<RndDossierDetail> {
  return hubFetch<RndDossierDetail>(
    `/rnd/dossiers/${dossierId}/sections/${encodeURIComponent(sectionKey)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ content_md: contentMd }),
    }
  );
}

export interface CommitteeMember {
  id: string;
  name: string;
  title: string;
  emoji: string;
  agent_id: string;
}

export interface CommitteeSession {
  id: string;
  dossier_id: string;
  session_id: string;
  title?: string | null;
  mode: string;
  active_section?: string | null;
  team: CommitteeMember[];
  status: "active" | "paused" | "closed";
  created_at?: string;
  closed_at?: string | null;
}

export interface CommitteeMessage {
  id: string;
  session_id: string;
  dossier_id: string;
  speaker: string;
  role: "user" | "assistant" | "system";
  content: string;
  section_key?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at?: string;
}

export async function startCommitteeSession(
  dossierId: string,
  body?: { mode?: string; active_section?: string | null; force_new?: boolean }
): Promise<{
  session: CommitteeSession;
  messages: CommitteeMessage[];
  resumed: boolean;
  read_only?: boolean;
}> {
  return hubFetch(`/rnd/dossiers/${dossierId}/committee/start`, {
    method: "POST",
    body: JSON.stringify(body ?? {}),
    timeoutMs: 120_000,
  });
}

export async function fetchCommitteeSession(
  dossierId: string,
  sessionId: string
): Promise<{ session: CommitteeSession; messages: CommitteeMessage[] }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/committee/${sessionId}`);
}

export async function sendCommitteeMessage(
  dossierId: string,
  sessionId: string,
  message: string,
  targetSpeaker?: string
): Promise<{ user_message: CommitteeMessage; responses: CommitteeMessage[] }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/committee/${sessionId}/message`, {
    method: "POST",
    body: JSON.stringify({ message, target_speaker: targetSpeaker }),
    timeoutMs: 120_000,
  });
}

export async function generateCommitteeReport(
  dossierId: string,
  sessionId: string
): Promise<{ committee_report_md: string; message: CommitteeMessage }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/committee/${sessionId}/report`, {
    method: "POST",
    timeoutMs: 180_000,
  });
}

export async function closeCommitteeSession(
  dossierId: string,
  sessionId: string,
  options?: { applySections?: boolean; generateCeoPackage?: boolean }
): Promise<{
  session: CommitteeSession | null;
  synthesis_md: string;
  committee_report_md?: string;
  sections_updated: string[];
  dossier_status: string;
  ceo_package?: { message: string } | null;
  ceo_package_error?: string | null;
}> {
  return hubFetch(`/rnd/dossiers/${dossierId}/committee/${sessionId}/close`, {
    method: "POST",
    body: JSON.stringify({
      apply_sections: options?.applySections ?? true,
      generate_ceo_package: options?.generateCeoPackage ?? true,
    }),
    timeoutMs: 180_000,
  });
}

export interface CeoPackageResponse {
  dossier_id: string;
  dossier_status: string;
  ceo_status: string;
  ceo_note?: string | null;
  dispatch_status: string;
  committee_report_md?: string | null;
  package?: Record<string, unknown> | null;
  dispatch?: Record<string, unknown> | null;
  markdown?: string | null;
  can_generate: boolean;
  can_decide: boolean;
  can_dispatch: boolean;
}

export interface CeoPendingDossier {
  id: string;
  slug: string;
  title: string;
  domain: string;
  branch?: string | null;
  status: DossierStatus;
  ceo_status: string;
  recommendation?: string | null;
  updated_at?: string;
  can_decide: boolean;
  has_committee_report?: boolean;
  needs_action?: "generate_package";
}

export interface CeoQueueResponse {
  to_validate: CeoPendingDossier[];
  to_prepare: CeoPendingDossier[];
}

function listItemToCeoPending(
  d: RndDossierListItem,
  needsAction?: "generate_package"
): CeoPendingDossier {
  return {
    id: d.id,
    slug: d.slug,
    title: d.title,
    domain: d.domain,
    status: d.status,
    ceo_status: d.ceo_status,
    can_decide: d.status === "ready_for_ceo",
    needs_action: needsAction,
  };
}

function buildCeoQueueFromDossierList(
  items: RndDossierListItem[],
  limit: number
): CeoQueueResponse {
  const to_validate: CeoPendingDossier[] = [];
  const to_prepare: CeoPendingDossier[] = [];

  for (const d of items) {
    if (d.ceo_status !== "pending") continue;
    if (d.status === "ceo_approved" || d.status === "ceo_rejected") continue;

    if (d.status === "ready_for_ceo") {
      to_validate.push(listItemToCeoPending(d));
    } else if (
      d.status === "partial_validated" ||
      d.status === "draft" ||
      d.status === "committee_active"
    ) {
      to_prepare.push(listItemToCeoPending(d, "generate_package"));
    }

    if (to_validate.length >= limit && to_prepare.length >= limit) break;
  }

  return {
    to_validate: to_validate.slice(0, limit),
    to_prepare: to_prepare.slice(0, limit),
  };
}

function isCeoQueueRouteMissing(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  const m = err.message.toLowerCase();
  return m.includes("not found") || m.includes("introuvable") || m.includes("route api introuvable");
}

export async function loadCeoQueueFromDossiers(
  limit = 20
): Promise<CeoQueueResponse> {
  const items = await fetchRndDossiers();
  return buildCeoQueueFromDossierList(items, limit);
}

export async function fetchCeoQueue(limit = 20): Promise<CeoQueueResponse> {
  try {
    const queue = await hubFetch<CeoQueueResponse>(
      `/rnd/ceo/queue?limit=${limit}`
    );
    if (queue?.to_validate || queue?.to_prepare) {
      return queue;
    }
  } catch (err) {
    if (!isCeoQueueRouteMissing(err)) {
      throw err;
    }
  }
  try {
    const viaDossiers = await hubFetch<CeoQueueResponse | RndDossierListItem[]>(
      `/rnd/dossiers?ceo_queue=true&limit=${limit}`
    );
    if (
      viaDossiers &&
      !Array.isArray(viaDossiers) &&
      (viaDossiers.to_validate || viaDossiers.to_prepare)
    ) {
      return viaDossiers;
    }
  } catch {
    // fall through to client-side build
  }
  return loadCeoQueueFromDossiers(limit);
}

export async function fetchCeoPendingDossiers(
  limit = 20
): Promise<CeoPendingDossier[]> {
  const queue = await fetchCeoQueue(limit);
  return queue.to_validate;
}

export function ceoDossierHref(dossier: { slug?: string; id: string }, view = "ceo"): string {
  const ref = dossier.slug || dossier.id;
  return `/rd?dossier=${encodeURIComponent(ref)}&view=${view}`;
}

export async function fetchCeoPackage(dossierId: string): Promise<CeoPackageResponse> {
  return hubFetch(`/rnd/dossiers/${dossierId}/ceo/package`);
}

export async function generateCeoPackage(
  dossierId: string,
  options?: { force?: boolean }
): Promise<{ message: string; package?: Record<string, unknown>; markdown?: string }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/ceo/generate`, {
    method: "POST",
    body: JSON.stringify({ force: options?.force ?? false }),
    timeoutMs: 120_000,
  });
}

export async function decideCeoPackage(
  dossierId: string,
  body: { ceo_status: "approved" | "rejected" | "pivot_requested"; ceo_note?: string }
): Promise<{ message: string; ceo_status: string; dossier_status: string }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/ceo/decide`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function dispatchToCoo(
  dossierId: string
): Promise<{ message: string; roadmap_items?: Array<{ id: string; title: string }> }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/ceo/dispatch`, {
    method: "POST",
    timeoutMs: 60_000,
  });
}

export async function executeDispatchAgents(
  dossierId: string
): Promise<{ message: string; execution_run_id?: string | null }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/ceo/execute`, {
    method: "POST",
    timeoutMs: 30_000,
  });
}

export interface EngineeringSpecResult {
  engineering_spec_md: string;
  stack: string;
  task_breakdown: Array<Record<string, unknown>>;
  qa_verdict?: string | null;
}

export interface PrdDecomposeResult {
  message: string;
  created_count: number;
  skipped_count: number;
  repo_slug: string;
  github_repo: string;
  build_manifest_path?: string;
  dry_run?: boolean;
}

export async function generateEngineeringSpec(
  dossierId: string,
  options?: { force?: boolean; debateRounds?: number }
): Promise<{ message: string; task_count: number; engineering_spec?: EngineeringSpecResult }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/engineering-spec/generate`, {
    method: "POST",
    body: JSON.stringify({
      force: options?.force ?? false,
      debate_rounds: options?.debateRounds ?? 1,
    }),
    timeoutMs: 180_000,
  });
}

export async function decomposePrdToIssues(
  dossierId: string,
  options?: {
    repoSlug?: string;
    dryRun?: boolean;
    markReadyCount?: number;
    forceSpec?: boolean;
  }
): Promise<PrdDecomposeResult> {
  return hubFetch(`/rnd/dossiers/${dossierId}/engineering-spec/decompose`, {
    method: "POST",
    body: JSON.stringify({
      repo_slug: options?.repoSlug,
      dry_run: options?.dryRun ?? false,
      mark_ready_count: options?.markReadyCount ?? 3,
      force_spec: options?.forceSpec ?? false,
    }),
    timeoutMs: 120_000,
  });
}

export async function fetchBuildManifest(
  dossierId: string
): Promise<{
  slug: string;
  has_engineering_spec: boolean;
  task_count: number;
  build_manifest: Record<string, unknown>;
}> {
  return hubFetch(`/rnd/dossiers/${dossierId}/build-manifest`);
}

export interface RndDossierAsset {
  id: string;
  dossier_id: string;
  section_key?: string | null;
  asset_type: string;
  file_path: string;
  public_url?: string | null;
  image_prompt?: string | null;
  generation_model?: string | null;
  width?: number | null;
  height?: number | null;
  metadata?: { label?: string; skipped_existing?: boolean } | null;
  created_at?: string | null;
  file_url?: string;
}

export async function fetchDossierAssets(dossierId: string): Promise<RndDossierAsset[]> {
  return hubFetch(`/rnd/dossiers/${dossierId}/assets`);
}

export async function generateDossierAssets(
  dossierId: string,
  options?: { force?: boolean }
): Promise<{
  dossier_id: string;
  assets: RndDossierAsset[];
  created: number;
  expected: number;
  message: string;
}> {
  return hubFetch(`/rnd/dossiers/${dossierId}/assets/generate`, {
    method: "POST",
    body: JSON.stringify({ force: options?.force ?? false }),
    timeoutMs: 120_000,
  });
}

export function dossierAssetFileUrl(
  dossierId: string,
  assetType: string
): string {
  return hubPublicApiUrl(
    `/rnd/dossiers/${dossierId}/assets/file?asset_type=${encodeURIComponent(assetType)}`
  );
}

export interface RndProductPage {
  id: string;
  dossier_id: string;
  project_id?: string | null;
  slug: string;
  title: string;
  tagline?: string | null;
  description_html?: string | null;
  hero_asset_id?: string | null;
  hero_url?: string | null;
  features: Array<{ title: string; description: string }>;
  pricing_model?: string | null;
  faq: Array<{ question: string; answer: string }>;
  seo_title?: string | null;
  seo_description?: string | null;
  waitlist_enabled: boolean;
  published: boolean;
  published_at?: string | null;
  public_url?: string;
  waitlist_url?: string;
  project_slug?: string;
}

export interface RndProductStatusResponse {
  unlocked: boolean;
  dossier_status: string;
  ceo_status: string;
  message: string;
  page?: RndProductPage | null;
  can_generate: boolean;
  can_publish: boolean;
  can_unpublish: boolean;
  public_url?: string | null;
}

export async function fetchProductStatus(
  dossierId: string
): Promise<RndProductStatusResponse> {
  return hubFetch(`/rnd/dossiers/${dossierId}/product/status`);
}

export async function fetchProductPage(dossierId: string): Promise<{
  dossier_id: string;
  page: RndProductPage | null;
  message: string;
}> {
  return hubFetch(`/rnd/dossiers/${dossierId}/product`);
}

export async function generateProductPage(
  dossierId: string,
  options?: { force?: boolean; waitlistEnabled?: boolean }
): Promise<{ page: RndProductPage; message: string; created: boolean }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/product/generate`, {
    method: "POST",
    body: JSON.stringify({
      force: options?.force ?? false,
      waitlist_enabled: options?.waitlistEnabled,
    }),
    timeoutMs: 120_000,
  });
}

export async function publishProductPage(
  dossierId: string
): Promise<{ page: RndProductPage; message: string; public_url: string }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/product/publish`, {
    method: "POST",
    timeoutMs: 60_000,
  });
}

export async function unpublishProductPage(
  dossierId: string
): Promise<{ page: RndProductPage; message: string }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/product/unpublish`, {
    method: "POST",
  });
}

export async function fetchPublicProductPage(slug: string): Promise<RndProductPage> {
  return hubFetch<RndProductPage>(`/rnd/product/${encodeURIComponent(slug)}`);
}

export type RndPipelineStageStatus =
  | "done"
  | "in_progress"
  | "pending"
  | "locked"
  | "skipped";

export interface RndPipelineStage {
  id: string;
  phase: number;
  label: string;
  tab?: string;
  status: RndPipelineStageStatus;
  detail?: string;
  public_url?: string;
}

export interface RndPipelineResponse {
  dossier_id: string;
  dossier_slug: string;
  dossier_status: string;
  ceo_status: string;
  progress_pct: number;
  stages_done: number;
  stages_total: number;
  stages: RndPipelineStage[];
  next_action?: string | null;
  next_tab?: string | null;
  pipeline_complete: boolean;
}

export async function fetchDossierPipeline(
  dossierId: string
): Promise<RndPipelineResponse> {
  return hubFetch(`/rnd/dossiers/${dossierId}/pipeline`);
}

/* Vue table Dossiers (Phase 27, ROADMAP.md) — read model pré-joint côté
   backend (services/rnd_dossier_table.py) : score/verdict de l'idée liée,
   verdict Conseil (Phase 25, si une session d'évaluation existe pour cette
   idée), nombre de documents, extrait de la section marché. Un seul appel
   plutôt qu'un N+1 par dossier depuis le frontend. */
export interface RndDossierCouncilVote {
  verdict: "GO" | "MAYBE" | "NO";
  consensus_pct: number;
  votes_count: number;
}

export interface RndDossierTableRow {
  id: string;
  slug: string;
  title: string;
  tagline?: string | null;
  domain: string;
  branch?: string | null;
  status: DossierStatus;
  ceo_status: string;
  ceo_note?: string | null;
  updated_at?: string | null;
  idea_legacy_id: string | null;
  score: number | null;
  verdict: "GO" | "MAYBE" | "NO" | null;
  market_score?: number | null;
  feasibility_score?: number | null;
  vision_score?: number | null;
  incubator_stage?: string;
  agents_count: number;
  votes: RndDossierCouncilVote | null;
  documents_count: number;
  market_excerpt: string | null;
  prototype_label: string | null;
}

export async function fetchRndDossierTableView(params?: {
  status?: string;
  domain?: string;
  limit?: number;
}): Promise<RndDossierTableRow[]> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.domain) qs.set("domain", params.domain);
  qs.set("limit", String(params?.limit ?? 100));
  return hubFetch<RndDossierTableRow[]>(`/rnd/dossiers/table-view?${qs.toString()}`);
}

export async function fetchRndModuleHealth(): Promise<{
  status: string;
  module: string;
  checks: Record<string, unknown>;
}> {
  return hubFetch("/rnd/health");
}

export async function generateDossierDeck(
  dossierId: string,
  options?: { exportPdf?: boolean }
): Promise<RndDeckGenerateResult> {
  return hubFetch<RndDeckGenerateResult>(`/rnd/dossiers/${dossierId}/deck/generate`, {
    method: "POST",
    body: JSON.stringify({ export_pdf: options?.exportPdf ?? true }),
    timeoutMs: 120_000,
  });
}

export function dossierDeckFileUrl(dossierId: string, type: "html" | "pdf"): string {
  return hubPublicApiUrl(`/rnd/dossiers/${dossierId}/deck/file?type=${type}`);
}

export type SocialPhase =
  | "internal"
  | "behind_scenes"
  | "teaser"
  | "pre_launch"
  | "launch"
  | "post_launch";

export type SocialCalendarStatus =
  | "planned"
  | "generated"
  | "approved"
  | "published"
  | "cancelled";

export interface RndSocialCalendarItem {
  id: string;
  dossier_id: string;
  phase: SocialPhase;
  milestone?: string | null;
  planned_at?: string | null;
  post_id?: string | null;
  status: SocialCalendarStatus;
  notes?: string | null;
  created_at?: string | null;
  post?: {
    id: string;
    platform: string;
    text_content: string;
    status: string;
    scheduled_at?: string;
  } | null;
  platforms: string[];
  content_type?: string | null;
}

export function isSocialPipelineUnlocked(
  status: DossierStatus,
  ceoStatus?: string | null
): boolean {
  if (status === "ceo_approved" || status === "in_conception" || status === "published") {
    return true;
  }
  return ceoStatus === "approved";
}

export async function fetchSocialStatus(dossierId: string): Promise<{
  unlocked: boolean;
  dossier_status: string;
  ceo_status: string;
  message: string;
}> {
  return hubFetch(`/rnd/dossiers/${dossierId}/social/status`);
}

export async function fetchSocialCalendar(dossierId: string): Promise<RndSocialCalendarItem[]> {
  return hubFetch(`/rnd/dossiers/${dossierId}/social/calendar`);
}

export async function generateSocialCalendar(
  dossierId: string,
  body?: { force?: boolean; launch_date?: string }
): Promise<{
  calendar: RndSocialCalendarItem[];
  created: number;
  message: string;
  social_strategy_md?: string;
}> {
  return hubFetch(`/rnd/dossiers/${dossierId}/social/calendar/generate`, {
    method: "POST",
    body: JSON.stringify(body ?? {}),
    timeoutMs: 120_000,
  });
}

export async function generateSocialPost(
  dossierId: string,
  itemId: string
): Promise<{ post: Record<string, unknown>; message: string }> {
  return hubFetch(`/rnd/dossiers/${dossierId}/social/calendar/${itemId}/generate-post`, {
    method: "POST",
    body: JSON.stringify({}),
    timeoutMs: 120_000,
  });
}

export async function generateAllSocialPosts(dossierId: string): Promise<{
  generated_count: number;
  message: string;
}> {
  return hubFetch(`/rnd/dossiers/${dossierId}/social/generate-all`, {
    method: "POST",
    timeoutMs: 300_000,
  });
}
