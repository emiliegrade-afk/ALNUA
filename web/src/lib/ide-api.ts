import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";
import { parseHubApiError } from "./hub-api-error";

export interface IdeWorkspace {
  id: string;
  label: string;
  path: string;
  kind: string;
  readOnly: boolean;
  active: boolean;
}

export interface IdeTreeEntry {
  name: string;
  path: string;
  type: "dir" | "file";
}

export interface IdeFilePayload {
  workspace: string;
  path: string;
  content: string;
  readOnly: boolean;
  language: string;
}

export interface IdeLiveTask {
  task_id?: string;
  status?: string;
  issue_number?: number;
  title?: string;
  progress?: number;
  current_file?: string | null;
  recent_code?: string[];
  log?: string[];
  worktree_path?: string;
  agent_id?: string;
}

const CODING_AGENT_LABELS: Record<string, string> = {
  dev_app: "Théo",
  dev_backend: "Hao",
  dev_gaming: "Nova",
  embedded_dev: "Zara",
};

export function codingAgentLabel(agentId?: string): string {
  if (!agentId) return "Agent";
  return CODING_AGENT_LABELS[agentId] ?? agentId;
}

async function ideFetch<T>(path: string, init?: RequestInit): Promise<T> {
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

export async function fetchIdeWorkspaces(): Promise<IdeWorkspace[]> {
  const data = await ideFetch<{ workspaces: IdeWorkspace[] }>("/ide/workspaces");
  return data.workspaces;
}

export async function fetchIdeTree(
  workspace: string,
  path = ".",
): Promise<{ entries: IdeTreeEntry[]; readOnly: boolean }> {
  const q = new URLSearchParams({ workspace, path });
  return ideFetch(`/ide/tree?${q}`);
}

export async function fetchIdeFile(
  workspace: string,
  path: string,
): Promise<IdeFilePayload> {
  const q = new URLSearchParams({ workspace, path });
  return ideFetch(`/ide/file?${q}`);
}

export async function saveIdeFile(
  workspace: string,
  path: string,
  content: string,
): Promise<void> {
  await ideFetch("/ide/file", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace, path, content }),
  });
}

export async function runSandboxCommand(
  command: string,
  cwd = ".",
): Promise<{ exitCode: number; output: string }> {
  return ideFetch("/ide/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command, cwd }),
  });
}

export async function fetchIdeLive(): Promise<{
  active: IdeLiveTask[];
  hasAgentWork: boolean;
}> {
  const data = await ideFetch<{
    active: IdeLiveTask[];
    hasAgentWork: boolean;
  }>("/ide/live");
  return data;
}

export async function fetchIdeHermesCatalog(): Promise<{
  available: boolean;
  root: string | null;
  skills: Array<{ id: string; name: string; description: string }>;
}> {
  return ideFetch("/ide/hermes-skills");
}

export async function fetchIdeDiff(workspace: string): Promise<string> {
  const data = await ideFetch<{ diff: string }>(
    `/ide/diff?workspace=${encodeURIComponent(workspace)}`,
  );
  return data.diff ?? "";
}

export async function askCodingCoach(
  message: string,
  opts: {
    workspace: string;
    filePath?: string;
    fileContent?: string;
  },
): Promise<string> {
  const data = await ideFetch<{ reply: string }>("/ide/coach/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      workspace: opts.workspace,
      file_path: opts.filePath,
      file_content: opts.fileContent,
    }),
  });
  return data.reply;
}
