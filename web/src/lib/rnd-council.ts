import { hubFetch } from "./hub-fetch";

/* Moteur Conseil R&D (Phase 25, ROADMAP.md) — Conseil stratégique (débat
   libre) + Conseil IA (input structuré → vote). */

export type CouncilSessionKind = "strategic" | "evaluation";
export type CouncilVerdict = "GO" | "MAYBE" | "NO";

export interface CouncilSession {
  id: string;
  session_id: string;
  session_kind: CouncilSessionKind;
  title: string | null;
  topic: string | null;
  status: "active" | "paused" | "closed";
  team: { agent_id: string; name: string; role: string }[];
  created_at: string;
  closed_at: string | null;
}

export interface CouncilMessage {
  id: string;
  session_id: string;
  speaker: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata?: { name?: string; role_label?: string } | null;
  created_at: string;
}

export interface CouncilVote {
  id: string;
  session_id: string;
  agent_id: string;
  agent_name: string;
  verdict: CouncilVerdict;
  confidence_pct: number;
  axis_scores: {
    feasibility?: number | null;
    innovation?: number | null;
    roi?: number | null;
    risk?: number | null;
  } | null;
  stance_text: string;
  round_index: number;
  is_final: boolean;
}

export interface CouncilGauges {
  consensus_pct: number;
  feasibility_pct: number;
  innovation_pct: number;
  roi_pct: number;
  risk_pct: number;
  per_agent: {
    agent_id: string;
    name: string;
    verdict: CouncilVerdict;
    confidence_pct: number;
    stance_text: string;
  }[];
}

export interface CouncilPostMessageResult {
  session_id: string;
  messages: CouncilMessage[];
  votes: CouncilVote[];
}

export interface CouncilCloseResult {
  session_id: string;
  gauges: CouncilGauges;
  recommendation: CouncilVerdict;
  consensus_pct: number;
  /** false si aucun membre n'a pu répondre (LLM indisponible) — la
   * "Décision Collective" ne doit pas s'afficher comme un vrai verdict. */
  deliberated: boolean;
}

export async function startCouncilSession(params: {
  kind: CouncilSessionKind;
  topic?: string;
  idea_id?: string | null;
}): Promise<CouncilSession> {
  return hubFetch("/rnd/council/sessions", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function fetchCouncilSession(
  sessionId: string
): Promise<{ session: CouncilSession; messages: CouncilMessage[] }> {
  return hubFetch(`/rnd/council/sessions/${encodeURIComponent(sessionId)}`);
}

export async function postCouncilMessage(
  sessionId: string,
  message: string
): Promise<CouncilPostMessageResult> {
  return hubFetch(`/rnd/council/sessions/${encodeURIComponent(sessionId)}/message`, {
    method: "POST",
    body: JSON.stringify({ message }),
    timeoutMs: 90_000,
  });
}

export async function fetchCouncilGauges(sessionId: string): Promise<CouncilGauges> {
  return hubFetch(`/rnd/council/sessions/${encodeURIComponent(sessionId)}/gauges`);
}

export async function closeCouncilSession(sessionId: string): Promise<CouncilCloseResult> {
  return hubFetch(`/rnd/council/sessions/${encodeURIComponent(sessionId)}/close`, {
    method: "POST",
  });
}

export interface CouncilStructuredInput {
  budget_eur?: number | null;
  team_size?: number | null;
  timeframe_weeks?: number | null;
  product_type?: string;
}

export interface CouncilEvaluateResult extends CouncilCloseResult {
  debate: CouncilPostMessageResult;
}

export async function evaluateCouncilProject(params: {
  topic: string;
  structured_input: CouncilStructuredInput;
  idea_id?: string | null;
}): Promise<CouncilEvaluateResult> {
  return hubFetch("/rnd/council/evaluate", {
    method: "POST",
    body: JSON.stringify(params),
    timeoutMs: 120_000,
  });
}
