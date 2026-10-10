/**
 * Turn a finished task into a structured result card.
 *
 * Cards are data (kind + fields), never HTML: the UI decides the rendering, so
 * text produced by an agent or fetched from the web can't inject markup.
 */

import type { LiveTask } from "./live-api";
import {
  parseChart,
  parseDraft,
  parseImage,
  parseList,
  parseSummary,
  type ChartSeries,
  type DraftBrief,
  type ImageBrief,
  type ListBrief,
  type SummaryBrief,
} from "./live-cards-parse";

export type {
  ChartPoint,
  ChartSeries,
  DraftBrief,
  ImageBrief,
  ListBrief,
  SummaryBrief,
} from "./live-cards-parse";
export { parseChart, parseDraft, parseImage, parseList, parseSummary };

export const AGENT_LABELS: Record<string, string> = {
  secretary: "Nadia",
  coo: "Aria",
  plan: "Équipe (plan COO)",
};

export function agentLabel(agentId: string): string {
  return AGENT_LABELS[agentId] ?? agentId;
}

export interface PlanStep {
  ok: boolean;
  agent: string;
  detail: string;
}

export type ResultCard =
  | { kind: "text"; taskId: string; title: string; body: string }
  | {
      kind: "steps";
      taskId: string;
      title: string;
      summary: string;
      steps: PlanStep[];
    }
  | { kind: "chart"; taskId: string; title: string; series: ChartSeries }
  | { kind: "summary"; taskId: string; title: string; brief: SummaryBrief }
  | { kind: "list"; taskId: string; title: string; brief: ListBrief }
  | { kind: "image"; taskId: string; title: string; brief: ImageBrief }
  | { kind: "draft"; taskId: string; title: string; brief: DraftBrief }
  | { kind: "error"; taskId: string; title: string; message: string };

// Matches the lines written by services/live_tasks.py::_run_plan.
const STEP_LINE = /^\[(OK|ÉCHEC)\]\s+(\S+)\s+—\s*(.*)$/;

export function parsePlanResult(
  text: string,
): { summary: string; steps: PlanStep[] } | null {
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  if (lines.length < 2) return null;
  const steps: PlanStep[] = [];
  for (const line of lines.slice(1)) {
    const m = STEP_LINE.exec(line);
    if (!m) return null;
    steps.push({ ok: m[1] === "OK", agent: m[2], detail: m[3] });
  }
  return { summary: lines[0], steps };
}

function titleOf(task: LiveTask): string {
  const text = task.instruction.trim();
  return text.length > 80 ? `${text.slice(0, 79)}…` : text;
}

export function buildResultCard(task: LiveTask): ResultCard | null {
  if (task.status === "failed") {
    return {
      kind: "error",
      taskId: task.id,
      title: titleOf(task),
      message: task.error || "La tâche a échoué.",
    };
  }
  if (task.status !== "done") return null;

  const draft = parseDraft(task.result);
  if (draft) {
    return { kind: "draft", taskId: task.id, title: titleOf(task), brief: draft };
  }
  const image = parseImage(task.result);
  if (image) {
    return { kind: "image", taskId: task.id, title: titleOf(task), brief: image };
  }
  const chart = parseChart(task.result);
  if (chart) {
    return { kind: "chart", taskId: task.id, title: titleOf(task), series: chart };
  }
  const listed = parseList(task.result);
  if (listed) {
    return { kind: "list", taskId: task.id, title: titleOf(task), brief: listed };
  }
  const brief = parseSummary(task.result);
  if (brief) {
    return { kind: "summary", taskId: task.id, title: titleOf(task), brief };
  }

  if (task.agent_id === "plan") {
    const plan = parsePlanResult(task.result);
    if (plan) {
      return {
        kind: "steps",
        taskId: task.id,
        title: titleOf(task),
        summary: plan.summary,
        steps: plan.steps,
      };
    }
  }
  return { kind: "text", taskId: task.id, title: titleOf(task), body: task.result };
}

/** `now` is injected so a running task's timer can tick without re-fetching. */
export function durationSeconds(task: LiveTask, now: number = Date.now()): number | null {
  if (!task.started_at) return null;
  const start = Date.parse(task.started_at);
  const end = task.finished_at ? Date.parse(task.finished_at) : now;
  if (Number.isNaN(start) || Number.isNaN(end)) return null;
  return Math.max(0, Math.round((end - start) / 1000));
}
