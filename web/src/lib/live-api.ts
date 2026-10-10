/** Nadia Live client — background tasks (DEC-038, SPEC_JARVIS_LIVE). */

import { hubFetch } from "./hub-fetch";
import { hubPublicApiUrl } from "./hub-api-config";
import { extractOAuthUrl } from "./live-oauth";

export type LiveTaskStatus =
  | "queued"
  | "running"
  | "done"
  | "failed"
  | "cancelled";

/** Executors the Hub accepts (LIVE_TASK_AGENTS allowlist). */
export type LiveAgentId = "secretary" | "coo" | "plan";

export interface LiveTask {
  id: string;
  agent_id: string;
  instruction: string;
  status: LiveTaskStatus;
  session_id: string;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  finished_at: string | null;
  result: string;
  artifacts: string[];
  file_ids: string[];
  error: string;
}

const STATUSES: ReadonlySet<string> = new Set([
  "queued",
  "running",
  "done",
  "failed",
  "cancelled",
]);

/** Narrow an unknown payload to a LiveTask; the stream is untrusted input. */
export function toLiveTask(value: unknown): LiveTask | null {
  if (typeof value !== "object" || value === null) return null;
  const v = value as Record<string, unknown>;
  if (
    typeof v.id !== "string" ||
    typeof v.agent_id !== "string" ||
    typeof v.instruction !== "string" ||
    typeof v.status !== "string" ||
    !STATUSES.has(v.status)
  ) {
    return null;
  }
  const str = (x: unknown): string => (typeof x === "string" ? x : "");
  const nullable = (x: unknown): string | null =>
    typeof x === "string" ? x : null;
  return {
    id: v.id,
    agent_id: v.agent_id,
    instruction: v.instruction,
    status: v.status as LiveTaskStatus,
    session_id: str(v.session_id),
    created_at: str(v.created_at),
    updated_at: str(v.updated_at),
    started_at: nullable(v.started_at),
    finished_at: nullable(v.finished_at),
    result: str(v.result),
    artifacts: Array.isArray(v.artifacts)
      ? v.artifacts.filter((a): a is string => typeof a === "string")
      : [],
    file_ids: Array.isArray(v.file_ids)
      ? v.file_ids.filter((a): a is string => typeof a === "string")
      : [],
    error: str(v.error),
  };
}

export function parseTaskEvent(raw: string): LiveTask | null {
  try {
    return toLiveTask(JSON.parse(raw));
  } catch {
    return null;
  }
}

export async function listLiveAgents(): Promise<LiveAgentId[]> {
  const data = await hubFetch<{ agents: LiveAgentId[] }>("/live/agents");
  return data.agents ?? [];
}

export async function createLiveTask(body: {
  agent_id: LiveAgentId;
  instruction: string;
  session_id?: string;
  file_ids?: string[];
}): Promise<LiveTask> {
  const created = await hubFetch<unknown>("/live/tasks", {
    method: "POST",
    body: JSON.stringify(body),
  });
  const task = toLiveTask(created);
  if (!task) throw new Error("Réponse inattendue du Hub pour la tâche créée.");
  return task;
}

export async function getLiveTask(taskId: string): Promise<LiveTask> {
  const res = await hubFetch<unknown>(`/live/tasks/${encodeURIComponent(taskId)}`);
  const task = toLiveTask(res);
  if (!task) throw new Error("Réponse inattendue du Hub pour la tâche.");
  return task;
}

export async function listLiveTasks(limit = 10): Promise<LiveTask[]> {
  const res = await hubFetch<{ tasks?: unknown[] }>(`/live/tasks?limit=${limit}`);
  return (res.tasks ?? [])
    .map(toLiveTask)
    .filter((t): t is LiveTask => t !== null);
}

export type LivePersona = "nadia" | "aria";

/** Ephemeral voice credentials. The OpenAI API key never reaches the browser. */
export interface LiveUsage {
  max_minutes: number;
  used_seconds: number;
  remaining_seconds: number;
}

export interface LiveVoiceSession {
  client_secret: string;
  calls_url: string;
  expires_at: number | null;
  model: string;
  persona: LivePersona;
  voice: string;
  session_id: string;
  remaining_seconds: number | null;
}

function toUsage(raw: Record<string, unknown>): LiveUsage {
  const num = (x: unknown, fallback: number) => (typeof x === "number" ? x : fallback);
  return {
    max_minutes: num(raw.max_minutes, 30),
    used_seconds: num(raw.used_seconds, 0),
    remaining_seconds: num(raw.remaining_seconds, 0),
  };
}

export async function getLiveUsage(): Promise<LiveUsage> {
  return toUsage(await hubFetch<Record<string, unknown>>("/live/usage"));
}

export interface LiveAppAccess {
  ok: boolean;
  via?: string;
  detail?: string;
  account?: string | null;
  expected?: string | null;
  account_ok?: boolean;
}

export interface LiveAccess {
  internet: { ok: boolean; detail: string };
  apps: Record<string, LiveAppAccess>;
  ready: {
    research: boolean;
    mail: boolean;
    calendar: boolean;
    discord: boolean;
    instagram: boolean;
    linkedin: boolean;
  };
}

function asApp(raw: unknown): LiveAppAccess {
  const o = raw && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
  return {
    ok: o.ok === true,
    via: typeof o.via === "string" ? o.via : undefined,
    detail: typeof o.detail === "string" ? o.detail : undefined,
    account: typeof o.account === "string" ? o.account : null,
    expected: typeof o.expected === "string" ? o.expected : null,
    account_ok: typeof o.account_ok === "boolean" ? o.account_ok : undefined,
  };
}

export function toLiveAccess(raw: Record<string, unknown>): LiveAccess {
  const internet = (raw.internet ?? {}) as Record<string, unknown>;
  const appsRaw = (raw.apps ?? {}) as Record<string, unknown>;
  const ready = (raw.ready ?? {}) as Record<string, unknown>;
  return {
    internet: {
      ok: internet.ok === true,
      detail: typeof internet.detail === "string" ? internet.detail : "",
    },
    apps: Object.fromEntries(Object.entries(appsRaw).map(([k, v]) => [k, asApp(v)])),
    ready: {
      research: ready.research === true,
      mail: ready.mail === true,
      calendar: ready.calendar === true,
      discord: ready.discord === true,
      instagram: ready.instagram === true,
      linkedin: ready.linkedin === true,
    },
  };
}

export async function getLiveAccess(): Promise<LiveAccess> {
  return toLiveAccess(await hubFetch<Record<string, unknown>>("/live/access", { timeoutMs: 20_000 }));
}

export async function connectLiveApp(
  app: string,
): Promise<{ url: string; hint: string }> {
  const raw = await hubFetch<Record<string, unknown>>(
    `/live/connect/${encodeURIComponent(app)}`,
    { method: "POST" },
  );
  const blob = typeof raw.oauth_url === "string" ? raw.oauth_url : "";
  const extra = typeof raw.hint === "string" ? raw.hint : "";
  const url = extractOAuthUrl(blob) || (blob.startsWith("http") ? blob : "");
  if (!url) {
    throw new Error(extra || blob || "Lien OAuth manquant.");
  }
  return { url, hint: extra };
}

export async function endLiveSession(sessionId: string, seconds: number): Promise<LiveUsage> {
  return toUsage(
    await hubFetch<Record<string, unknown>>("/live/session/end", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, seconds }),
      keepalive: true,
    }),
  );
}

export async function createLiveSession(persona: LivePersona): Promise<LiveVoiceSession> {
  const raw = await hubFetch<Record<string, unknown>>("/live/session", {
    method: "POST",
    body: JSON.stringify({ persona }),
  });
  if (typeof raw.client_secret !== "string" || typeof raw.calls_url !== "string") {
    throw new Error("Réponse inattendue du Hub pour la session vocale.");
  }
  return {
    client_secret: raw.client_secret,
    calls_url: raw.calls_url,
    expires_at: typeof raw.expires_at === "number" ? raw.expires_at : null,
    model: typeof raw.model === "string" ? raw.model : "",
    persona,
    voice: typeof raw.voice === "string" ? raw.voice : "",
    session_id: typeof raw.session_id === "string" ? raw.session_id : "",
    remaining_seconds: typeof raw.remaining_seconds === "number" ? raw.remaining_seconds : null,
  };
}

export async function confirmLiveDraft(
  kind: "linkedin" | "email" | "pc_input",
  draftId: string,
): Promise<{ message: string }> {
  const raw = await hubFetch<Record<string, unknown>>("/live/confirm", {
    method: "POST",
    body: JSON.stringify({ kind, draft_id: draftId }),
  });
  return { message: typeof raw.message === "string" ? raw.message : "Fait." };
}

export async function cancelLiveTask(taskId: string): Promise<LiveTask> {
  const res = await hubFetch<unknown>(
    `/live/tasks/${encodeURIComponent(taskId)}/cancel`,
    { method: "POST" },
  );
  const task = toLiveTask(res);
  if (!task) throw new Error("Réponse inattendue du Hub pour l'annulation.");
  return task;
}

export interface LiveStreamHandlers {
  onTask: (task: LiveTask) => void;
  onOpen: () => void;
  onError: () => void;
}

export interface LiveStreamSource {
  addEventListener(type: string, listener: (e: MessageEvent) => void): void;
  onopen: ((ev: Event) => void) | null;
  onerror: ((ev: Event) => void) | null;
  close(): void;
}

/**
 * Subscribe to task changes. The Next.js /api/hub proxy injects X-Hub-Key, so a
 * plain EventSource works from the browser. Returns an unsubscribe function.
 */
export function openLiveStream(
  handlers: LiveStreamHandlers,
  factory: (url: string) => LiveStreamSource = (url) => new EventSource(url),
): () => void {
  const source = factory(hubPublicApiUrl("/live/tasks/stream"));
  source.onopen = () => handlers.onOpen();
  source.onerror = () => handlers.onError();
  source.addEventListener("task", (event) => {
    const task = parseTaskEvent(event.data as string);
    if (task) handlers.onTask(task);
  });
  return () => source.close();
}
