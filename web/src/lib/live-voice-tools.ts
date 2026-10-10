/**
 * Tools the voice model may call (declared server side in services/live_session.py).
 * They only ever talk to /live/tasks; the model never reaches anything else.
 */

import {
  cancelLiveTask,
  createLiveTask,
  getLiveTask,
  listLiveTasks,
  type LiveAgentId,
  type LiveTask,
} from "./live-api";

const AGENTS: ReadonlySet<string> = new Set(["secretary", "coo", "plan"]);
const RESULT_PREVIEW_CHARS = 600;
const INSTRUCTION_PREVIEW_CHARS = 80;

export interface VoiceToolApi {
  create: typeof createLiveTask;
  get: typeof getLiveTask;
  list: typeof listLiveTasks;
  cancel: typeof cancelLiveTask;
}

const defaultApi: VoiceToolApi = {
  create: createLiveTask,
  get: getLiveTask,
  list: listLiveTasks,
  cancel: cancelLiveTask,
};

function clip(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

function parseArgs(raw: string): Record<string, unknown> {
  try {
    const value: unknown = JSON.parse(raw || "{}");
    return typeof value === "object" && value !== null && !Array.isArray(value)
      ? (value as Record<string, unknown>)
      : {};
  } catch {
    return {};
  }
}

function summary(task: LiveTask) {
  return {
    task_id: task.id,
    agent: task.agent_id,
    status: task.status,
    instruction: clip(task.instruction, INSTRUCTION_PREVIEW_CHARS),
  };
}

/**
 * Run one tool call and return the JSON string sent back to the model. Never
 * throws: a failure becomes `{ error }` so the model can say so instead of hanging.
 * Task results are truncated and are data for the model, never instructions.
 */
export type VoiceToolContext = {
  /** Pièces jointes sélectionnées dans le composer Live avant l'appel vocal. */
  pendingFileIds?: () => string[];
  /** Vide les écrans (outil clear_screens) — ne touche pas aux tâches. */
  clearScreens?: () => void;
};

function mergeFileIds(
  fromModel: unknown,
  pending: string[] | undefined,
): string[] | undefined {
  const modelIds = Array.isArray(fromModel)
    ? fromModel.filter((x): x is string => typeof x === "string" && x.trim().length > 0)
    : [];
  const merged = [...new Set([...(pending ?? []), ...modelIds])];
  return merged.length ? merged.slice(0, 5) : undefined;
}

export async function runVoiceTool(
  call: { name: string; arguments: string },
  onTask: (task: LiveTask) => void = () => undefined,
  api: VoiceToolApi = defaultApi,
  ctx: VoiceToolContext = {},
): Promise<string> {
  const args = parseArgs(call.arguments);
  const taskId = typeof args.task_id === "string" ? args.task_id : "";
  try {
    switch (call.name) {
      case "start_task": {
        const agent = args.agent;
        const instruction = args.instruction;
        if (typeof agent !== "string" || !AGENTS.has(agent)) {
          return JSON.stringify({ error: "Agent non autorisé." });
        }
        const fileIds = mergeFileIds(args.file_ids, ctx.pendingFileIds?.());
        if (typeof instruction !== "string" || (!instruction.trim() && !fileIds?.length)) {
          return JSON.stringify({ error: "Instruction vide." });
        }
        const task = await api.create({
          agent_id: agent as LiveAgentId,
          instruction: instruction.trim() || "Voir les pièces jointes.",
          session_id: "live-voice",
          file_ids: fileIds,
        });
        onTask(task);
        return JSON.stringify(summary(task));
      }
      case "list_tasks": {
        const tasks = await api.list(8);
        return JSON.stringify({ tasks: tasks.map(summary) });
      }
      case "get_task_status": {
        if (!taskId) return JSON.stringify({ error: "task_id manquant." });
        const task = await api.get(taskId);
        return JSON.stringify({
          ...summary(task),
          result_preview: clip(task.result, RESULT_PREVIEW_CHARS),
          error: task.error,
        });
      }
      case "cancel_task": {
        if (!taskId) return JSON.stringify({ error: "task_id manquant." });
        const task = await api.cancel(taskId);
        onTask(task);
        return JSON.stringify(summary(task));
      }
      case "clear_screens": {
        ctx.clearScreens?.();
        return JSON.stringify({ cleared: true });
      }
      default:
        return JSON.stringify({ error: `Outil inconnu : ${call.name}` });
    }
  } catch (err) {
    return JSON.stringify({
      error: err instanceof Error ? err.message : "Échec de l'outil.",
    });
  }
}
