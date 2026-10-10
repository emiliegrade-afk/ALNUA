import type { ChatMessage } from "./types";
import { hubFetch } from "./hub-fetch";

export type AssistantAgentMode = "auto" | "coo" | "secretary";

export interface AssistantChatResult {
  agent_id: string;
  agent_name: string;
  response: string;
  response_id?: string;
  issue_created: boolean;
  issue_number?: number;
  issue_url?: string;
  repo?: string;
}

export async function sendAssistantMessage(
  message: string,
  agent: AssistantAgentMode = "auto",
  project?: string,
  fileIds?: string[],
): Promise<AssistantChatResult> {
  return hubFetch<AssistantChatResult>("/assistant/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      agent,
      project: project ?? null,
      file_ids: fileIds?.length ? fileIds : [],
    }),
    timeoutMs: 120_000,
  });
}

export async function submitAgentFeedback(params: {
  agent_id: string;
  response_id: string;
  rating: 1 | -1;
  comment?: string;
  original_message?: string;
  original_response?: string;
}): Promise<{ id: string; recorded: boolean; regen_triggered: boolean; regen_response?: string }> {
  return hubFetch("/feedback/agent", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export type { ChatMessage };
