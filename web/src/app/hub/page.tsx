"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { Play, Loader2 } from "lucide-react";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { BureauOfficeHero } from "@/components/openroom/bureau-office-hero";
import { BureauPage } from "@/components/shared/bureau-page";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchGithubPrs,
  fetchPipelineIssues,
  fetchPipelineStatus,
  fetchWeeklyCosts,
  runPipelineIssue,
  type GithubPr,
  type PipelineIssue,
} from "@/lib/lobby-api";

const HubWorkflowsPanel = dynamic(
  () =>
    import("@/components/hub/hub-workflows-panel").then((m) => ({
      default: m.HubWorkflowsPanel,
    })),
  {
    loading: () => (
      <p className="mb-6 text-sm text-titanium/60">Chargement Company OS…</p>
    ),
  }
);

const HubAutomationPanel = dynamic(
  () =>
    import("@/components/hub/hub-automation-panel").then((m) => ({
      default: m.HubAutomationPanel,
    })),
  {
    loading: () => (
      <p className="mb-6 text-sm text-titanium/60">Chargement automations…</p>
    ),
  }
);

const ProductionOpsCockpit = dynamic(
  () =>
    import("@/components/hub/production-ops-cockpit").then((m) => ({
      default: m.ProductionOpsCockpit,
    })),
  {
    loading: () => (
      <p className="mb-6 text-sm text-titanium/60">Chargement ops production…</p>
    ),
  }
);

const CeoCockpitPanel = dynamic(
  () =>
    import("@/components/hub/ceo-cockpit").then((m) => ({
      default: m.CeoCockpitPanel,
    })),
  {
    loading: () => (
      <p className="mb-6 text-sm text-titanium/60">Chargement cockpit CEO…</p>
    ),
  }
);

const PIPELINE_TASK_KEY = "alnua-pipeline-task-id";
const TERMINAL_STATUSES = new Set(["completed", "failed"]);

export default function HubPage() {
  const [issues, setIssues] = useState<PipelineIssue[]>([]);
  const [prs, setPrs] = useState<GithubPr[]>([]);
  const [costs, setCosts] = useState<{
    total_usd?: number;
    by_day?: Array<Record<string, string | number>>;
  } | null>(null);
  const [pipelineLog, setPipelineLog] = useState<string[]>([]);
  const [pipelineProgress, setPipelineProgress] = useState(0);
  const [pipelineStatus, setPipelineStatus] = useState<string | null>(null);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [runningIssue, setRunningIssue] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [issueData, prData, costData] = await Promise.all([
        fetchPipelineIssues(),
        fetchGithubPrs(),
        fetchWeeklyCosts(),
      ]);
      setIssues(issueData);
      setPrs(prData);
      setCosts(costData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de charger le hub.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const saved = sessionStorage.getItem(PIPELINE_TASK_KEY);
    if (saved) {
      setActiveTaskId(saved);
    }
  }, []);

  useEffect(() => {
    if (!activeTaskId) return;

    let cancelled = false;

    async function poll() {
      const status = await fetchPipelineStatus(activeTaskId!);
      if (!status || cancelled) return;

      setPipelineLog(status.log);
      setPipelineProgress(status.progress);
      setPipelineStatus(status.status);

      if (TERMINAL_STATUSES.has(status.status)) {
        sessionStorage.removeItem(PIPELINE_TASK_KEY);
        setActiveTaskId(null);
        setRunningIssue(null);
        void load();
      }
    }

    void poll();
    const interval = setInterval(() => {
      void poll();
    }, 3000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [activeTaskId, load]);

  function issueKey(issue: PipelineIssue): string {
    return `${issue._repo_slug ?? "hub"}-${issue.number}`;
  }

  async function handleRun(issue: PipelineIssue) {
    const key = issueKey(issue);
    setRunningIssue(key);
    setPipelineLog([]);
    setPipelineProgress(0);
    setPipelineStatus("starting");
    try {
      const result = await runPipelineIssue(issue.number, issue._repo_slug);
      sessionStorage.setItem(PIPELINE_TASK_KEY, result.task_id);
      setActiveTaskId(result.task_id);
    } catch {
      setPipelineLog([`Échec lancement issue #${issue.number}`]);
      setPipelineStatus("failed");
      setRunningIssue(null);
    }
  }

  return (
    <BureauPage
      dept="hub"
      title="Direction"
      subtitle="Aria · Sam · Léon · Alex · Pipeline"
    >
      <BureauOfficeHero agentId="coo" />

      <BureauAgentsSection
        bureau="hub"
        excludeAgentIds={["coo"]}
        className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      />

      <HubWorkflowsPanel />
      <HubAutomationPanel />

      <CeoCockpitPanel />

      <ProductionOpsCockpit />

      {loading ? (
        <p className="mb-4 font-body text-sm text-titanium/60">Chargement…</p>
      ) : null}
      {error ? (
        <p className="mb-4 font-body text-sm text-red-400">{error}</p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader>
            <CardTitle className="font-title text-base text-ivory">
              Pipeline Codage
            </CardTitle>
            <p className="label-caps">Issues agent-ready</p>
          </CardHeader>
          <CardContent className="space-y-4">
            {issues.length === 0 ? (
              <p className="text-sm text-gray-500">Aucune issue prête.</p>
            ) : (
              <ul className="space-y-2">
                {issues.map((issue) => (
                  <li
                    key={issueKey(issue)}
                    className="flex items-center justify-between gap-2 rounded-lg border border-copper/10 px-3 py-2"
                  >
                    <span className="font-body text-sm text-ivory/80">
                      {issue._repo_name ? `[${issue._repo_name}] ` : ""}
                      #{issue.number} — {issue.title}
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={runningIssue === issueKey(issue)}
                      onClick={() => handleRun(issue)}
                      className="shrink-0 border-copper/30 hover:border-copper/50"
                    >
                      {runningIssue === issueKey(issue) ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Play className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </li>
                ))}
              </ul>
            )}

            <div>
              <p className="mb-2 text-xs font-medium text-gray-500">
                PRs ouvertes ({prs.length})
              </p>
              {prs.length === 0 ? (
                <p className="text-sm text-gray-500">Aucune PR.</p>
              ) : (
                <ul className="space-y-1">
                  {prs.slice(0, 5).map((pr) => (
                    <li
                      key={`${pr.repo_slug ?? "hub"}-${pr.number}`}
                      className="text-xs text-gray-400"
                    >
                      {pr.repo_name ? `[${pr.repo_name}] ` : ""}#{pr.number} —{" "}
                      {pr.title}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {(activeTaskId || pipelineLog.length > 0) && (
              <div>
                <div className="mb-2 flex items-center justify-between text-xs font-medium text-gray-500">
                  <span>Log pipeline</span>
                  {pipelineStatus && (
                    <span className="text-gray-400">
                      {pipelineStatus} · {pipelineProgress}%
                    </span>
                  )}
                </div>
                <div className="mb-2 h-1.5 overflow-hidden rounded-full bg-obsidian-deep/70">
                  <div
                    className="h-full rounded-full bg-copper/70 transition-all duration-500"
                    style={{ width: `${pipelineProgress}%` }}
                  />
                </div>
                <div className="max-h-32 overflow-y-auto rounded-lg bg-obsidian-deep/70 p-2 font-mono text-[11px] text-gray-500">
                  {pipelineLog.length === 0
                    ? "Démarrage…"
                    : pipelineLog.map((line, i) => (
                        <div key={i}>{line}</div>
                      ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader>
            <CardTitle className="font-title text-base text-ivory">
              Coûts LLM — 7 jours
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 font-title text-2xl font-semibold text-ivory">
              ${(costs?.total_usd ?? 0).toFixed(4)}
            </p>
            {costs?.by_day && costs.by_day.length > 0 ? (
              <div className="space-y-2">
                {costs.by_day.map((day) => (
                  <div
                    key={String(day.date)}
                    className="flex items-center justify-between text-xs text-gray-400"
                  >
                    <span>{day.date}</span>
                    <span>
                      $
                      {Object.entries(day)
                        .filter(([k]) => k !== "date")
                        .reduce((sum, [, v]) => sum + Number(v), 0)
                        .toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">Pas de données cette semaine.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </BureauPage>
  );
}
