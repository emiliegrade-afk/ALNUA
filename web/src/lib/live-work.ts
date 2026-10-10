/**
 * How a live task should be labelled on screen so parallel jobs stay distinct
 * (research vs mail vs agenda), like the Jarvis demo's activity tiles.
 */

import type { LiveTask } from "./live-api";

export type LiveWorkKind =
  | "research"
  | "open"
  | "mail"
  | "calendar"
  | "plan"
  | "write"
  | "chart"
  | "summary"
  | "image"
  | "other";

const RULES: { kind: LiveWorkKind; re: RegExp }[] = [
  { kind: "open", re: /\b(ouvre|ouvrir|open)\b/i },
  {
    kind: "research",
    re: /\b(recherche|veille|internet|web|google|actualit|news|cherche|trouve[- ]moi)\b/i,
  },
  { kind: "mail", re: /\b(e-?mails?|mails?|inbox|courrier|gmail)\b/i },
  {
    kind: "calendar",
    re: /\b(agenda|calendrier|r[eé]union|rdv|emploi du temps|cr[eé]neau)\b/i,
  },
  { kind: "write", re: /\b(r[eé]dige|poste|linkedin|article|brouillon)\b/i },
  {
    kind: "image",
    re: /\b(g[eé]n[eè]re|illustration|visuel|photo libre|image libre)\b/i,
  },
  { kind: "chart", re: /\b(graphique|graphe|courbe|histogramme|chart)\b/i },
  { kind: "summary", re: /\b(r[eé]sum[eé]|synth[eè]se|brief)\b/i },
];

export const WORK_LABEL: Record<LiveWorkKind, string> = {
  research: "Recherche internet",
  open: "Ouvrir",
  mail: "Mails",
  calendar: "Agenda",
  plan: "Plan d'équipe",
  write: "Rédaction",
  chart: "Graphique",
  summary: "Résumé",
  image: "Image",
  other: "Tâche",
};

export function workKind(task: Pick<LiveTask, "agent_id" | "instruction">): LiveWorkKind {
  if (task.agent_id === "plan") return "plan";
  for (const rule of RULES) {
    if (rule.re.test(task.instruction)) return rule.kind;
  }
  return "other";
}

export function workTitle(task: Pick<LiveTask, "agent_id" | "instruction">): string {
  const kind = workKind(task);
  const clipped =
    task.instruction.length > 72 ? `${task.instruction.slice(0, 71)}…` : task.instruction;
  return kind === "other" ? clipped : `${WORK_LABEL[kind]} — ${clipped}`;
}
