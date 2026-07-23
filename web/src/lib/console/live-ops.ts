import type { LobbyStats } from "@/lib/lobby-api";
import type { AgentStatus, AgentsStatusResponse } from "@/lib/openroom-api";
import type { ConsoleActivityItem } from "./types";
import type { DeployStatus, Incident, Severity } from "./rich-data-static";

function inferSeverity(message: string): Severity {
  const m = message.toLowerCase();
  if (/critical|critique|intrusion|down|arrêt/.test(m)) return "critical";
  if (/warn|alert|latence|élevé|failed|erreur/.test(m)) return "warning";
  return "info";
}

export function buildLiveIncidents(
  feed: ConsoleActivityItem[],
  agents: Record<string, AgentStatus>,
  stats: LobbyStats,
): Incident[] {
  const items: Incident[] = [];

  if (!stats.apiOnline) {
    items.push({
      id: "hub-offline",
      severity: "critical",
      title: "API Hub hors ligne",
      pôle: "CONNECTIVITÉ",
      time: "maintenant",
      resolved: false,
    });
  } else if (!stats.apiAuthenticated) {
    items.push({
      id: "hub-key",
      severity: "warning",
      title: "Clé API Hub manquante côté Next.js",
      pôle: "CONNECTIVITÉ",
      time: "maintenant",
      resolved: false,
    });
  }

  for (const [agentId, agent] of Object.entries(agents)) {
    if (agent.status === "error") {
      items.push({
        id: `agent-err-${agentId}`,
        severity: "warning",
        title: agent.currentTask || `Agent ${agentId} en erreur`,
        pôle: agentId.toUpperCase(),
        time: "récent",
        resolved: false,
      });
    }
  }

  for (const item of feed) {
    if (item.kind !== "alert") continue;
    items.push({
      id: item.id,
      severity: inferSeverity(item.action),
      title: item.action.slice(0, 120),
      pôle: item.dept,
      time: item.time,
      resolved: /résolu|fixed|ok\b/i.test(item.action),
    });
  }

  if (items.length === 0) {
    items.push({
      id: "no-incidents",
      severity: "info",
      title: "Aucune alerte active",
      pôle: "HUB",
      time: "—",
      resolved: true,
    });
  }

  return items.slice(0, 8);
}

export function buildLiveDeployments(
  feed: ConsoleActivityItem[],
  coding?: AgentsStatusResponse["codingPipeline"],
): Array<{
  id: string;
  service: string;
  version: string;
  by: string;
  time: string;
  status: DeployStatus;
}> {
  const items: Array<{
    id: string;
    service: string;
    version: string;
    by: string;
    time: string;
    status: DeployStatus;
  }> = [];

  for (const issue of coding?.inPipelineIssues ?? []) {
    items.push({
      id: `gh-${issue.issue_number ?? items.length}`,
      service: issue.repo_slug || "GitHub",
      version: `#${issue.issue_number ?? "?"}`,
      by: issue.title?.slice(0, 40) || "Pipeline",
      time: "en cours",
      status: "running",
    });
  }

  if ((coding?.githubFailed ?? 0) > 0) {
    items.push({
      id: "gh-failed",
      service: "GitHub Academy",
      version: `${coding!.githubFailed} échec(s)`,
      by: "Pipeline",
      time: "récent",
      status: "failed",
    });
  }

  for (const item of feed) {
    if (item.kind !== "ship") continue;
    items.push({
      id: item.id,
      service: "Release",
      version: item.action.slice(0, 32),
      by: item.agent,
      time: item.time,
      status: /fail|échec/i.test(item.action) ? "failed" : "success",
    });
  }

  if (items.length === 0) {
    items.push({
      id: "no-deploy",
      service: "—",
      version: "Aucun déploiement",
      by: "Hub",
      time: "—",
      status: "success",
    });
  }

  return items.slice(0, 8);
}

export function buildLiveDecisionsToday(feed: ConsoleActivityItem[]): Array<{
  id: string;
  title: string;
  agent: string;
  time: string;
  status: "approved" | "review" | "pending";
}> {
  const decisions = feed.filter((i) => i.kind === "decide" || i.kind === "ship");

  if (decisions.length === 0) {
    return [
      {
        id: "no-decisions",
        title: "Aucune décision enregistrée aujourd'hui",
        agent: "—",
        time: "—",
        status: "pending",
      },
    ];
  }

  return decisions.slice(0, 6).map((item) => ({
    id: item.id,
    title: item.action.slice(0, 100),
    agent: item.agent,
    time: item.time,
    status: /valid|approuv|ship|merge/i.test(item.action)
      ? "approved"
      : /review|revue/i.test(item.action)
        ? "review"
        : "pending",
  }));
}
