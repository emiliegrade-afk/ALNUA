import type { HqSector } from "@/lib/hq-hub-offices";
import type { LobbyStats } from "@/lib/lobby-api";
import type { AgentsStatusResponse, OpenRoomLogEntry } from "@/lib/openroom-api";

export interface DeptMetric {
  label: string;
  value: string;
  live?: boolean;
}

/** Bucket recent log activity into a sparkline (newest → right). */
export function activitySparkline(
  logs: OpenRoomLogEntry[],
  buckets = 12,
): number[] {
  const result = Array.from({ length: buckets }, () => 0);
  if (logs.length === 0) return result;

  logs.forEach((_, i) => {
    const bucket = Math.min(
      buckets - 1,
      Math.floor((i / Math.max(logs.length, 1)) * buckets),
    );
    result[buckets - 1 - bucket] += 1;
  });
  return result;
}

export function pipelineBars(
  coding: AgentsStatusResponse["codingPipeline"],
): { label: string; value: number }[] {
  if (!coding) {
    return [
      { label: "Actif", value: 0 },
      { label: "Queue", value: 0 },
      { label: "Prêt", value: 0 },
      { label: "Fail", value: 0 },
    ];
  }
  return [
    { label: "Actif", value: coding.activeTasks },
    { label: "Queue", value: coding.githubInPipeline },
    { label: "Prêt", value: coding.githubAgentReady },
    { label: "Fail", value: coding.githubFailed },
  ];
}

/** Contextual KPI tiles for the selected office (or global fallback). */
export function deptMetrics(
  office: HqSector | null,
  stats: LobbyStats,
  coding: AgentsStatusResponse["codingPipeline"],
  activeAgents: number,
): DeptMetric[] {
  const costTodayUsd = Number(stats.costTodayUsd ?? 0);
  const costToday = `$${costTodayUsd.toFixed(2)}`;
  const pipelineActive = (coding?.activeTasks ?? 0) > 0;

  if (!office) {
    return [
      { label: "API", value: stats.apiOnline ? "Online" : "Offline", live: stats.apiOnline },
      { label: "Actifs", value: String(activeAgents), live: activeAgents > 0 },
      { label: "Coût/j", value: costToday, live: costTodayUsd > 0 },
      { label: "PR", value: String(stats.hubPrCount), live: stats.hubPrCount > 0 },
      { label: "Tickets", value: String(stats.appOpenTickets), live: stats.appOpenTickets > 0 },
      { label: "Apps", value: String(stats.connectedApps) },
    ];
  }

  switch (office.id) {
    case "direction":
    case "hub":
      return [
        { label: "PR Hub", value: String(stats.hubPrCount), live: stats.hubPrCount > 0 },
        { label: "Pipeline", value: pipelineActive ? "Actif" : "Idle", live: pipelineActive },
        { label: "Queue GH", value: String(coding?.githubInPipeline ?? 0), live: (coding?.githubInPipeline ?? 0) > 0 },
        { label: "Coût/j", value: costToday, live: costTodayUsd > 0 },
      ];
    case "app":
      return [
        { label: "Tickets", value: String(stats.appOpenTickets), live: stats.appOpenTickets > 0 },
        { label: "PR", value: String(stats.hubPrCount), live: stats.hubPrCount > 0 },
        { label: "Coût/j", value: costToday },
        { label: "Pipeline", value: pipelineActive ? "Actif" : "Idle", live: pipelineActive },
      ];
    case "marketing":
      return [
        { label: "Posts", value: String(stats.marketingPendingPosts), live: stats.marketingPendingPosts > 0 },
        { label: "Coût/j", value: costToday },
        { label: "Apps", value: String(stats.connectedApps) },
      ];
    case "rd":
      return [
        { label: "Sessions", value: String(stats.rdSessions), live: stats.rdSessions > 0 },
        { label: "Coût/j", value: costToday },
        { label: "Queue GH", value: String(coding?.githubInPipeline ?? 0) },
      ];
    case "finances":
      return [
        { label: "Mois", value: stats.financesMonthTotal, live: stats.financesMonthTotal !== "$0.00" },
        { label: "Coût/j", value: costToday, live: costTodayUsd > 0 },
      ];
    case "brand":
      return [
        { label: "Kits", value: String(stats.brandKits), live: stats.brandKits > 0 },
        { label: "Coût/j", value: costToday },
      ];
    case "connections":
      return [
        { label: "Apps", value: String(stats.connectedApps), live: stats.connectedApps > 0 },
        { label: "API", value: stats.apiOnline ? "Online" : "Offline", live: stats.apiOnline },
      ];
    case "ceo":
      return [
        { label: "Notifs", value: String(stats.ceoNotifications), live: stats.ceoNotifications > 0 },
        { label: "Coût/j", value: costToday },
        { label: "PR", value: String(stats.hubPrCount), live: stats.hubPrCount > 0 },
      ];
    case "secretary":
      return [
        { label: "Notifs", value: String(stats.ceoNotifications), live: stats.ceoNotifications > 0 },
        { label: "Coût/j", value: costToday },
        { label: "Apps", value: String(stats.connectedApps) },
      ];
    default:
      return [
        { label: "Coût/j", value: costToday },
        { label: "API", value: stats.apiOnline ? "Online" : "Offline", live: stats.apiOnline },
        { label: "Pipeline", value: pipelineActive ? "Actif" : "Idle", live: pipelineActive },
      ];
  }
}
