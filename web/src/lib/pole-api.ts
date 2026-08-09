/**
 * Pole department APIs — direct agent endpoints (no COO delegation).
 */
import { hubFetch } from "./hub-fetch";
import { fetchGithubPrs, fetchPipelineIssues, fetchEveStatus, runPipelineIssue } from "./lobby-api";

// ---------------------------------------------------------------------------
// Shared
// ---------------------------------------------------------------------------
export interface AgentInstructionResponse {
  result: string;
}

export function postAgentInstruction<T = unknown>(
  path: string,
  body: Record<string, unknown>,
  timeoutMs = 120_000
): Promise<T> {
  return hubFetch<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs,
  });
}

// ---------------------------------------------------------------------------
// Secretary (Nadia)
// ---------------------------------------------------------------------------
export function secretaryDraftEmail(body: {
  subject: string;
  context: string;
  recipient: string;
  tone?: string;
  language?: string;
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/secretary/draft-email", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 90_000,
  });
}

export function secretaryTriageEmails(
  emails: Array<{ from: string; subject: string; body: string }>
): Promise<Record<string, unknown>> {
  return hubFetch("/agents/secretary/triage-emails", {
    method: "POST",
    body: JSON.stringify({ emails }),
    timeoutMs: 90_000,
  });
}

export function secretaryDraftContract(body: {
  contract_type: string;
  party_name: string;
  scope: string;
  duration: string;
  compensation?: string;
  special_clauses?: string;
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/secretary/draft-contract", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 90_000,
  });
}

export function secretaryPlanMeeting(body: {
  participants: string[];
  topic: string;
  duration_minutes?: number;
  constraints?: string;
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/secretary/plan-meeting", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 90_000,
  });
}

export function secretaryMeetingNotes(body: {
  meeting_title: string;
  raw_notes: string;
  participants: string[];
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/secretary/meeting-notes", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 90_000,
  });
}

// ---------------------------------------------------------------------------
// Dev Backend (Hao)
// ---------------------------------------------------------------------------
export function devBackendDesignApi(body: {
  feature: string;
  project: string;
  constraints?: string;
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/dev-backend/design-api", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}

export function devBackendImplement(body: {
  feature: string;
  project: string;
  api_spec?: string;
  tech_stack?: string;
}): Promise<{ result: string }> {
  return hubFetch("/agents/dev-backend/implement", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 180_000,
  });
}

export function devBackendReview(body: {
  code: string;
  context?: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>("/agents/dev-backend/review", body);
}

export function devBackendDebug(body: {
  error: string;
  context: string;
  code_snippet?: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>("/agents/dev-backend/debug", body);
}

// ---------------------------------------------------------------------------
// Dev App (Théo)
// ---------------------------------------------------------------------------
export function devAppInstruction(instruction: string): Promise<AgentInstructionResponse> {
  return postAgentInstruction<AgentInstructionResponse>(
    "/agents/dev-app/instruction",
    { instruction },
    180_000
  );
}

export function devAppListIssues(): Promise<{ issues: unknown[] }> {
  return hubFetch("/agents/dev-app/issues");
}

// ---------------------------------------------------------------------------
// Dev Gaming (Suki)
// ---------------------------------------------------------------------------
export function devGamingInstruction(instruction: string): Promise<AgentInstructionResponse> {
  return postAgentInstruction<AgentInstructionResponse>(
    "/agents/dev-gaming/instruction",
    { instruction },
    180_000
  );
}

// ---------------------------------------------------------------------------
// Level Designer (Finn)
// ---------------------------------------------------------------------------
export function levelDesignerQuest(body: {
  quest_name: string;
  game: string;
  lore_context?: string;
  player_level_range?: string;
  quest_type?: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>("/agents/level-designer/quest", body);
}

export function levelDesignerLore(body: {
  subject: string;
  game: string;
  lore_type?: string;
  length?: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>("/agents/level-designer/lore", body);
}

export function levelDesignerLevel(body: {
  level_name: string;
  game: string;
  biome?: string;
  difficulty?: string;
  special_mechanics?: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>("/agents/level-designer/level", body);
}

export function levelDesignerBalance(body: {
  system: string;
  current_values: Record<string, unknown>;
  player_feedback?: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>("/agents/level-designer/balance", body);
}

// ---------------------------------------------------------------------------
// Marketing (Lena)
// ---------------------------------------------------------------------------
export function marketingInstruction(instruction: string): Promise<AgentInstructionResponse> {
  return postAgentInstruction<AgentInstructionResponse>(
    "/agents/marketing/instruction",
    { instruction },
    120_000
  );
}

export function marketingSeoAudit(url: string): Promise<{ result: string }> {
  return hubFetch("/agents/marketing/seo-audit", {
    method: "POST",
    body: JSON.stringify({ url }),
    timeoutMs: 120_000,
  });
}

export function marketingCreateContent(body: {
  type: string;
  project: string;
  topic: string;
  tone?: string;
  length?: string;
}): Promise<{ result: string }> {
  return hubFetch("/agents/marketing/content", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}

// ---------------------------------------------------------------------------
// Ads (Léo) — Phase 33, ROADMAP.md
// ---------------------------------------------------------------------------
export interface AdsCreateCampaignResponse {
  ok: boolean;
  status: string;
  creative_variations: { variant: string; hook: string; cta: string }[];
  campaign?: import("./marketing-api").Campaign;
  error?: string;
}

export function adsCreateCampaign(body: {
  brief: string;
  platform?: string;
  budget_usd?: number;
  objective?: string;
  audience?: string;
  project_id?: string;
  name?: string;
}): Promise<AdsCreateCampaignResponse> {
  return hubFetch("/agents/ads/create-campaign", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}

// ---------------------------------------------------------------------------
// Hardware / Embedded (Robo)
// ---------------------------------------------------------------------------
export function hardwareInstruction(instruction: string): Promise<AgentInstructionResponse> {
  return postAgentInstruction<AgentInstructionResponse>(
    "/agents/hardware/instruction",
    { instruction },
    120_000
  );
}

export function embeddedInstruction(instruction: string): Promise<AgentInstructionResponse> {
  return postAgentInstruction<AgentInstructionResponse>(
    "/agents/embedded/instruction",
    { instruction },
    120_000
  );
}

export function embeddedPiCommand(command: string): Promise<Record<string, unknown>> {
  return hubFetch("/agents/embedded/pi-command", {
    method: "POST",
    body: JSON.stringify({ command }),
    timeoutMs: 60_000,
  });
}

export interface BomItem {
  id: string;
  component: string;
  category: string;
  quantity: number;
  unit_price: number | null;
  supplier: string | null;
  url: string | null;
  status: string;
  notes: string | null;
  total_price?: number | null;
}

export interface BomTotals {
  total_eur: number;
  by_category: Record<string, number>;
  count: number;
}

export function fetchBomItems(): Promise<{ items: BomItem[]; totals: BomTotals }> {
  return hubFetch("/bom/eve");
}

export function createBomItem(body: {
  component: string;
  category: string;
  quantity?: number;
  unit_price?: number | null;
  supplier?: string;
  url?: string;
  status?: string;
  notes?: string;
}): Promise<BomItem> {
  return hubFetch("/bom/eve", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateBomItem(
  id: string,
  body: Partial<{
    component: string;
    category: string;
    quantity: number;
    unit_price: number | null;
    supplier: string;
    url: string;
    status: string;
    notes: string;
  }>
): Promise<BomItem> {
  return hubFetch(`/bom/eve/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function deleteBomItem(id: string): Promise<{ ok: boolean }> {
  return hubFetch(`/bom/eve/${id}`, { method: "DELETE" });
}

export function eveAlternatives(
  need: string,
  category?: string,
  maxOptions = 4,
): Promise<Record<string, unknown>> {
  return hubFetch("/agents/electronics/alternatives", {
    method: "POST",
    body: JSON.stringify({ need, category, max_options: maxOptions }),
    timeoutMs: 90_000,
  });
}

export function eveAssemblyPlan(goal = ""): Promise<Record<string, unknown>> {
  return hubFetch("/agents/mechanical/assembly-plan", {
    method: "POST",
    body: JSON.stringify({ goal }),
    timeoutMs: 90_000,
  });
}

export function eveInfraBlueprint(focus = "full"): Promise<Record<string, unknown>> {
  return hubFetch("/agents/hardware/infra-blueprint", {
    method: "POST",
    body: JSON.stringify({ focus }),
    timeoutMs: 90_000,
  });
}

export function fetchPiBridgeStatus(): Promise<{
  configured: boolean;
  host: string | null;
  message: string;
  tooling: { agents: string; human_files: string };
}> {
  return hubFetch("/robo/pi-bridge");
}

/** Vague B Phase 21 — lab / BOM / Pi probes (honest empty). */
export function qaRobotLabContext(body?: {
  project_id?: string;
  category?: string;
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/qa-robot/lab-context", {
    method: "POST",
    body: JSON.stringify(body || {}),
  });
}

export function safetyLabContext(body?: {
  project_id?: string;
  category?: string;
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/safety/lab-context", {
    method: "POST",
    body: JSON.stringify(body || {}),
  });
}

export function visionAiPiProbe(command = "uname -a"): Promise<Record<string, unknown>> {
  return hubFetch("/agents/vision-ai/pi-probe", {
    method: "POST",
    body: JSON.stringify({ command }),
  });
}

export function mechanicalBomContext(category?: string): Promise<Record<string, unknown>> {
  return hubFetch("/agents/mechanical/bom-context", {
    method: "POST",
    body: JSON.stringify({ category, limit: 20 }),
  });
}

export interface LookingGlassStatus {
  connected: boolean;
  holoplay_running: boolean;
  message: string;
}

export function fetchLookingGlassStatus(): Promise<LookingGlassStatus> {
  return hubFetch("/looking-glass/status");
}

// ---------------------------------------------------------------------------
// Controller (Finances — Rémi)
// ---------------------------------------------------------------------------
export function controllerAnalyzeCosts(body: {
  period: string;
  costs_data: Record<string, unknown>;
  budget?: Record<string, number>;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>("/agents/controller/costs", body);
}

export function controllerForecast(body: {
  project: string;
  horizon_months?: number;
  assumptions: string;
  historical_data?: Record<string, unknown>;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>("/agents/controller/forecast", body);
}

export function controllerLlmAlert(body: {
  daily_spend: number;
  monthly_budget: number;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>("/agents/controller/llm-alert", body);
}

export function controllerMonthlyReport(body: {
  month: string;
  all_data: Record<string, unknown>;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>(
    "/agents/controller/monthly-report",
    body,
    120_000
  );
}

// ---------------------------------------------------------------------------
// Comptabilité (Jules)
// ---------------------------------------------------------------------------
export function accountingFinancialAdvice(body: {
  month: string;
  financial_summary: Record<string, unknown>;
  question: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction<Record<string, unknown>>(
    "/agents/accounting/advice",
    body,
    90_000
  );
}

export function accountingListInvoices(
  status = "to_pay",
): Promise<Record<string, unknown>> {
  return hubFetch(
    `/agents/accounting/invoices?status=${encodeURIComponent(status)}`,
  );
}

// ---------------------------------------------------------------------------
// Analytics — Layla (business)
// ---------------------------------------------------------------------------
export function analystBusinessMarket(body: {
  product: string;
  market: string;
  competitors?: string[];
}): Promise<Record<string, unknown>> {
  return postAgentInstruction("/agents/analyst-business/market", body);
}

export function analystBusinessKpis(body: {
  project: string;
  stage: string;
  business_goal: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction("/agents/analyst-business/kpis", body);
}

export function analystBusinessUserResearch(body: {
  product: string;
  research_question: string;
  user_segment?: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction("/agents/analyst-business/user-research", body);
}

export function analystBusinessBrief(body: {
  topic: string;
  context: string;
  decision_needed: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction("/agents/analyst-business/brief", body, 90_000);
}

// ---------------------------------------------------------------------------
// Analytics — Axel (data)
// ---------------------------------------------------------------------------
export function analystDataSql(body: {
  question: string;
  schema_context?: string;
  db_type?: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction("/agents/analyst-data/sql", {
    ...body,
    db_type: body.db_type ?? "postgresql",
  });
}

export function analystDataFunnel(body: {
  funnel_name: string;
  steps: string[];
  data: Record<string, unknown>;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction("/agents/analyst-data/funnel", body);
}

export function analystDataAnomaly(body: {
  metric: string;
  recent_values: number[];
  baseline?: string;
  period?: string;
}): Promise<Record<string, unknown>> {
  return postAgentInstruction("/agents/analyst-data/anomaly", body);
}

export function analystDataDashboard(body: {
  dashboard_name: string;
  audience: string;
  kpis: string[];
  data_sources: string[];
}): Promise<Record<string, unknown>> {
  return postAgentInstruction("/agents/analyst-data/dashboard-spec", body, 90_000);
}

// ---------------------------------------------------------------------------
// Orchestration (pilotage automatique)
// ---------------------------------------------------------------------------
export interface OrchestrationWorkflow {
  id: string;
  name: string;
  endpoint: string;
  trigger: string;
  agents: string[];
  level: number;
}

export function fetchOrchestrationWorkflows(): Promise<OrchestrationWorkflow[]> {
  return hubFetch("/orchestration/workflows");
}

export function runMorningOrchestration(
  weeklyPlan = false
): Promise<Record<string, unknown>> {
  return hubFetch("/orchestration/morning", {
    method: "POST",
    body: JSON.stringify({ weekly_plan: weeklyPlan }),
    timeoutMs: 180_000,
  });
}

export function runBriefingMorning(weeklyPlan = false): Promise<Record<string, unknown>> {
  return hubFetch(`/briefing/morning-run?weekly_plan=${weeklyPlan}`, {
    method: "POST",
    timeoutMs: 180_000,
  });
}

// ---------------------------------------------------------------------------
// Reviews / Bots
// ---------------------------------------------------------------------------
export function syncStoreReviews(projectId?: string): Promise<{ ingested: number }> {
  return hubFetch("/reviews/sync", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId ?? null }),
    timeoutMs: 120_000,
  });
}

export function runPublisherCycle(): Promise<{ published: number; failed: number }> {
  return hubFetch("/bots/publisher/run", { method: "POST", timeoutMs: 60_000 });
}

export function runAnalyticsCycle(): Promise<{ metrics_recorded: number }> {
  return hubFetch("/bots/analytics/run", { method: "POST", timeoutMs: 60_000 });
}

// ---------------------------------------------------------------------------
// App pole helpers
// ---------------------------------------------------------------------------
export { fetchGithubPrs, fetchPipelineIssues, fetchEveStatus, runPipelineIssue };
