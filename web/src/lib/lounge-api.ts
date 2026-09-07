import { hubFetch } from "./hub-fetch";

/** Client Agent Lounge — scores / sessions / puzzles (DEC-031, Phase 46). */

export interface LoungeLeaderboardEntry {
  agent_id: string;
  first_name: string;
  last_name: string;
  team: string;
  score: number;
  rank: number;
  level: number;
  badges: string[];
}

export interface LoungeProfile {
  agent_id: string;
  first_name: string;
  last_name: string;
  team: string;
  score: number;
  level: number;
  badges: string[];
  month: string;
}

export interface LoungeSession {
  id: string;
  agent_id: string;
  activity: string;
  status: "active" | "completed" | string;
  puzzle_id?: string;
  puzzle_title?: string;
  puzzle_prompt?: string;
  difficulty?: number;
  started_at?: string;
  completed_at?: string | null;
  won?: boolean | null;
  agent_answer?: string | null;
  points_awarded?: number | null;
  score_action?: string | null;
  correct_answer?: string;
  llm_error?: string;
}

export interface LoungePuzzle {
  id: string;
  title: string;
  difficulty: number;
  prompt: string;
}

export function fetchLoungeLeaderboard(
  month?: string,
): Promise<LoungeLeaderboardEntry[]> {
  const q = month ? `?month=${encodeURIComponent(month)}` : "";
  return hubFetch(`/lounge/leaderboard${q}`);
}

export function fetchLoungeTeamLeaderboard(
  month?: string,
): Promise<
  {
    team_id: string;
    team_label: string;
    total_score: number;
    rank: number;
  }[]
> {
  const q = month ? `?month=${encodeURIComponent(month)}` : "";
  return hubFetch(`/lounge/leaderboard/teams${q}`);
}

export function fetchLoungeProfile(agentId: string): Promise<LoungeProfile> {
  return hubFetch(`/lounge/profile/${encodeURIComponent(agentId)}`);
}

export function fetchLoungePuzzles(): Promise<LoungePuzzle[]> {
  return hubFetch("/lounge/puzzles");
}

export function fetchActiveLoungeSessions(): Promise<LoungeSession[]> {
  return hubFetch("/lounge/sessions/active");
}

export function startLoungeSession(body: {
  agent_id: string;
  activity?: string;
  puzzle_id?: string;
  challenge_id?: string;
  run_now?: boolean;
}): Promise<LoungeSession> {
  return hubFetch("/lounge/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type LoungeTournament = {
  id: string;
  title: string;
  detail: string;
  activity?: string;
  when_label: string;
  starts_at?: string;
  reward_xp?: number;
  status?: string;
};

export function fetchLoungeTournaments(): Promise<LoungeTournament[]> {
  return hubFetch("/lounge/tournaments");
}

export function runLoungeSession(sessionId: string): Promise<LoungeSession> {
  return hubFetch(`/lounge/sessions/${encodeURIComponent(sessionId)}/run`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function completeLoungeSession(
  sessionId: string,
  answer: string,
): Promise<LoungeSession> {
  return hubFetch(`/lounge/sessions/${encodeURIComponent(sessionId)}/complete`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });
}

export type LoungeDept =
  | "app"
  | "rd"
  | "gaming"
  | "robo"
  | "marketing"
  | "hub"
  | "finances"
  | "analytics";

export function proposeLoungeFinding(body: {
  session_id: string;
  dept: LoungeDept;
  summary: string;
  project_id?: string;
  agent_id?: string;
}): Promise<{
  ok: boolean;
  message: string;
  proposal: Record<string, unknown>;
  ticket?: Record<string, unknown> | null;
}> {
  return hubFetch("/lounge/propose", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
