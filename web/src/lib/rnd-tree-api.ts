import { hubFetch } from "./hub-fetch";

export type HypothesisNodeStatus =
  | "pending"
  | "running"
  | "explored"
  | "pruned"
  | "merged"
  | "failed";

export interface HypothesisNode {
  id: string;
  parent_id: string | null;
  title: string;
  hypothesis: string;
  status: HypothesisNodeStatus;
  depth: number;
  score: number | null;
  verdict: string | null;
  insight: string;
  evidence: {
    key_findings?: { finding: string; confidence?: string; source?: string }[];
    recommended_actions?: string[];
  };
  report_markdown?: string | null;
  children: string[];
  idea_id?: string | null;
  dossier_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RndTreeSummary {
  slug: string;
  topic: string;
  status: string;
  created_at: string;
  updated_at?: string;
  node_count: number;
  merged_count: number;
  pruned_count: number;
}

export interface RndTreeDetail {
  id: string;
  slug: string;
  topic: string;
  status: string;
  root_id: string;
  requested_by: string;
  watch_topics: string[];
  nodes: HypothesisNode[];
  stats: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface RndWatchTopic {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  url?: string;
  suggested_branches?: string[];
  added_at?: string;
}

export interface GraphNode {
  id: string;
  parent_id: string | null;
  title: string;
  status: HypothesisNodeStatus;
  score: number | null;
  verdict: string | null;
  depth: number;
  idea_id?: string | null;
  dossier_id?: string | null;
  x: number;
  y: number;
}

export interface RndTreeGraph {
  slug: string;
  topic: string;
  root_id: string;
  nodes: GraphNode[];
  edges: { from: string; to: string }[];
  width: number;
  height: number;
}

export interface LlmBenchmarkResult {
  id: string;
  ran_at: string;
  agent_id: string;
  model: string;
  openrouter: {
    runs: Array<{
      prompt_index: number;
      prompt_preview: string;
      elapsed_ms: number;
      approx_output_tokens: number;
      tokens_per_second: number;
      error?: string;
    }>;
    avg_elapsed_ms: number | null;
    avg_tokens_per_second: number | null;
  };
  diffusion_gemma_reference: {
    model: string;
    published_tokens_per_second_rtx5090: number;
    note: string;
    url?: string;
  };
  comparison: {
    diffusion_gemma_estimated_speedup_vs_openrouter: number | null;
    use_diffusion_gemma_for: string[];
    keep_openrouter_for: string[];
  };
  recommendation: string;
}

export async function fetchRndTrees(limit = 20): Promise<{ trees: RndTreeSummary[] }> {
  return hubFetch(`/rnd/trees?limit=${limit}`);
}

export async function fetchRndTree(slug: string): Promise<RndTreeDetail> {
  return hubFetch(`/rnd/trees/${encodeURIComponent(slug)}`);
}

export async function fetchRndTreeGraph(slug: string): Promise<RndTreeGraph> {
  return hubFetch(`/rnd/trees/${encodeURIComponent(slug)}/graph`);
}

export async function startRndInvestigation(
  topic: string
): Promise<{ success: boolean; slug: string; message: string }> {
  return hubFetch("/rnd/investigate", {
    method: "POST",
    body: JSON.stringify({ topic, requested_by: "ceo" }),
    timeoutMs: 30_000,
  });
}

export async function expandRndNode(
  slug: string,
  nodeId: string,
  options?: {
    maxChildren?: number;
    runAfter?: boolean;
    title?: string;
    hypothesis?: string;
  }
): Promise<{ success: boolean; children_created: number }> {
  return hubFetch(`/rnd/trees/${encodeURIComponent(slug)}/nodes/${encodeURIComponent(nodeId)}/expand`, {
    method: "POST",
    body: JSON.stringify({
      max_children: options?.maxChildren ?? 3,
      run_after: options?.runAfter ?? false,
      title: options?.title,
      hypothesis: options?.hypothesis,
    }),
    timeoutMs: 60_000,
  });
}

export async function runRndNode(
  slug: string,
  nodeId: string
): Promise<{ success: boolean; status: string }> {
  return hubFetch(
    `/rnd/trees/${encodeURIComponent(slug)}/nodes/${encodeURIComponent(nodeId)}/run`,
    { method: "POST", timeoutMs: 15_000 }
  );
}

export async function patchRndNodeStatus(
  slug: string,
  nodeId: string,
  status: HypothesisNodeStatus
): Promise<{ success: boolean }> {
  return hubFetch(`/rnd/trees/${encodeURIComponent(slug)}/nodes/${encodeURIComponent(nodeId)}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function promoteRndNode(
  slug: string,
  nodeId: string
): Promise<{
  success: boolean;
  dossier_id: string;
  message?: string;
  already?: boolean;
}> {
  return hubFetch(
    `/rnd/trees/${encodeURIComponent(slug)}/nodes/${encodeURIComponent(nodeId)}/promote?enrich=true`,
    { method: "POST", timeoutMs: 90_000 }
  );
}

export async function reparentRndNode(
  slug: string,
  nodeId: string,
  newParentId: string
): Promise<{ success: boolean; node_id: string; new_parent_id: string }> {
  return hubFetch(
    `/rnd/trees/${encodeURIComponent(slug)}/nodes/${encodeURIComponent(nodeId)}/reparent`,
    {
      method: "PATCH",
      body: JSON.stringify({ new_parent_id: newParentId }),
    }
  );
}

export async function fetchRndWatchTopics(): Promise<{ topics: RndWatchTopic[] }> {
  return hubFetch("/rnd/watch-topics");
}

export async function runLlmLatencyBenchmark(): Promise<LlmBenchmarkResult> {
  return hubFetch("/rnd/benchmark/llm-latency", {
    method: "POST",
    body: JSON.stringify({ agent_id: "secretary" }),
    timeoutMs: 120_000,
  });
}

export async function fetchLatestLlmBenchmark(): Promise<{
  benchmark: LlmBenchmarkResult | null;
  message?: string;
}> {
  return hubFetch("/rnd/benchmark/llm-latency/latest");
}
