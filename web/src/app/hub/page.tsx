"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Play, Loader2 } from "lucide-react";
import { AgentCard } from "@/components/shared/agent-card";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchGithubPrs,
  fetchPipelineIssues,
  fetchWeeklyCosts,
  runPipelineIssue,
} from "@/lib/lobby-api";

const HUB_AGENTS = [
  {
    icon: "🎯",
    name: "COO Agent",
    role: "Chief Operating Officer",
    branch: "hub" as const,
    description: "Orchestration globale, délégation et priorisation.",
    skills: ["Délégation", "Briefing", "Pipeline"],
  },
  {
    icon: "📋",
    name: "PM Agent",
    role: "Project Manager",
    branch: "hub" as const,
    description: "Triage tickets, roadmap et suivi des livrables.",
    skills: ["Triage", "Roadmap", "Priorisation"],
  },
  {
    icon: "🔍",
    name: "QA Agent",
    role: "Quality Assurance",
    branch: "hub" as const,
    description: "Analyse feedbacks, bugs et qualité produit.",
    skills: ["Feedback", "Bugs", "Tests"],
  },
  {
    icon: "📝",
    name: "Spec Agent",
    role: "Spécifications",
    branch: "hub" as const,
    description: "Rédaction specs techniques et prompts Cursor.",
    skills: ["Specs", "Cursor", "Architecture"],
  },
];

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export default function HubPage() {
  const [issues, setIssues] = useState<
    Array<{ number: number; title: string }>
  >([]);
  const [prs, setPrs] = useState<
    Array<{ number: number; title: string; html_url?: string }>
  >([]);
  const [costs, setCosts] = useState<{
    total_usd?: number;
    by_day?: Array<Record<string, string | number>>;
  } | null>(null);
  const [pipelineLog, setPipelineLog] = useState<string[]>([]);
  const [runningIssue, setRunningIssue] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

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
    const wsUrl = API_URL.replace(/^http/, "ws") + "/ws/pipeline";
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as { message?: string };
        if (data.message) {
          setPipelineLog((prev) => [...prev.slice(-19), data.message!]);
        }
      } catch {
        /* ignore malformed */
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, []);

  async function handleRun(issueNumber: number) {
    setRunningIssue(issueNumber);
    try {
      await runPipelineIssue(issueNumber);
      setPipelineLog((prev) => [
        ...prev,
        `Pipeline lancé sur issue #${issueNumber}`,
      ]);
    } catch {
      setPipelineLog((prev) => [
        ...prev,
        `Échec lancement issue #${issueNumber}`,
      ]);
    } finally {
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
          <AgentCard key={agent.name} {...agent} />
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
                    key={issue.number}
                    className="flex items-center justify-between gap-2 rounded-lg border border-copper/10 px-3 py-2"
                  >
                    <span className="font-body text-sm text-ivory/80">
                      #{issue.number} — {issue.title}
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={runningIssue === issue.number}
                      onClick={() => handleRun(issue.number)}
                      className="shrink-0 border-copper/30 hover:border-copper/50"
                    >
                      {runningIssue === issue.number ? (
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
                    <li key={pr.number} className="text-xs text-gray-400">
                      #{pr.number} — {pr.title}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div>
              <p className="mb-2 text-xs font-medium text-gray-500">
                Log live
              </p>
              <div className="max-h-32 overflow-y-auto rounded-lg bg-black/30 p-2 font-mono text-[11px] text-gray-500">
                {pipelineLog.length === 0
                  ? "En attente de connexion WebSocket…"
                  : pipelineLog.map((line, i) => (
                      <div key={i}>{line}</div>
                    ))}
              </div>
            </div>
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
    </>
  );
}
