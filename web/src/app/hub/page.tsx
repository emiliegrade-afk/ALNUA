"use client";

import { useCallback, useEffect, useState } from "react";
import { Play, Loader2 } from "lucide-react";
import { AgentCard } from "@/components/shared/agent-card";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { AgentFocusPanel } from "@/components/openroom/agent-focus-panel";
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
import { fetchAgentsStatus, type AgentStatus } from "@/lib/openroom-api";

const PIPELINE_TASK_KEY = "alnua-pipeline-task-id";
const TERMINAL_STATUSES = new Set(["completed", "failed"]);
const POLL_MS = 3000;

const HUB_AGENTS = [
  {
    id: "coo",
    icon: "🎯",
    name: "COO Agent",
    role: "Chief Operating Officer",
    branch: "hub" as const,
    description: "Orchestration globale, délégation et priorisation.",
    skills: ["Délégation", "Briefing", "Pipeline"],
  },
  {
    id: "pm",
    icon: "📋",
    name: "PM Agent",
    role: "Project Manager",
    branch: "hub" as const,
    description: "Triage tickets, roadmap et suivi des livrables.",
    skills: ["Triage", "Roadmap", "Priorisation"],
  },
  {
    id: "qa",
    icon: "🔍",
    name: "QA Agent",
    role: "Quality Assurance",
    branch: "hub" as const,
    description: "Analyse feedbacks, bugs et qualité produit.",
    skills: ["Feedback", "Bugs", "Tests"],
  },
  {
    id: "spec",
    icon: "📝",
    name: "Spec Agent",
    role: "Spécifications",
    branch: "hub" as const,
    description: "Rédaction specs techniques et prompts Cursor.",
    skills: ["Specs", "Cursor", "Architecture"],
  },
];

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
  const [focusedAgentId, setFocusedAgentId] = useState<string | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});

  const load = useCallback(async () => {
    const [issueData, prData, costData] = await Promise.all([
      fetchPipelineIssues(),
      fetchGithubPrs(),
      fetchWeeklyCosts(),
    ]);
    setIssues(issueData);
    setPrs(prData);
    setCosts(costData);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const data = await fetchAgentsStatus();
      if (cancelled) return;
      setAgentStatuses(data.agents);
    }

    void poll();
    const interval = setInterval(() => void poll(), POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

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
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="hub"
        title="Direction"
        subtitle="Agents centraux · Pipeline codage · QA"
      />

      <section className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {HUB_AGENTS.map((agent) => (
          <AgentCard
            key={agent.id}
            {...agent}
            status={agentStatuses[agent.id]?.status ?? "idle"}
            currentTask={agentStatuses[agent.id]?.currentTask}
            onClick={() => setFocusedAgentId(agent.id)}
          />
        ))}
      </section>

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
                <div className="mb-2 h-1.5 overflow-hidden rounded-full bg-black/30">
                  <div
                    className="h-full rounded-full bg-copper/70 transition-all duration-500"
                    style={{ width: `${pipelineProgress}%` }}
                  />
                </div>
                <div className="max-h-32 overflow-y-auto rounded-lg bg-black/30 p-2 font-mono text-[11px] text-gray-500">
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

      {focusedAgentId ? (
        <AgentFocusPanel
          agent={{
            id: focusedAgentId,
            name: HUB_AGENTS.find((a) => a.id === focusedAgentId)!.name,
            emoji: HUB_AGENTS.find((a) => a.id === focusedAgentId)!.icon,
            role: HUB_AGENTS.find((a) => a.id === focusedAgentId)!.role,
          }}
          status={agentStatuses[focusedAgentId] ?? { status: "idle" }}
          onClose={() => setFocusedAgentId(null)}
        />
      ) : null}
    </>
  );
}
