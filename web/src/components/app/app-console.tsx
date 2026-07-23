"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink, GitBranch, Loader2 } from "lucide-react";
import { AgentActionConsole } from "@/components/shared/agent-action-console";
import { ROUTES } from "@/lib/routes";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  devAppInstruction,
  devAppListIssues,
  devBackendDebug,
  devBackendDesignApi,
  devBackendImplement,
  devBackendReview,
  fetchGithubPrs,
  fetchPipelineIssues,
  runPipelineIssue,
} from "@/lib/pole-api";
import { toast } from "sonner";

export function AppConsole() {
  const [issues, setIssues] = useState<
    Array<{ number: number; title: string; repo_slug?: string }>
  >([]);
  const [prs, setPrs] = useState<Array<{ number: number; title: string; html_url?: string }>>(
    []
  );
  const [pipelineRunning, setPipelineRunning] = useState<number | null>(null);

  const load = useCallback(async () => {
    const [ready, prList, pipeline] = await Promise.all([
      devAppListIssues().catch(() => ({ issues: [] })),
      fetchGithubPrs().catch(() => []),
      fetchPipelineIssues().catch(() => []),
    ]);
    const fromPipeline = pipeline.map((i) => ({
      number: i.number,
      title: i.title,
      repo_slug: i._repo_slug,
    }));
    const fromReady = (ready.issues as Array<{ number: number; title: string; repo_slug?: string }>) ?? [];
    setIssues(fromPipeline.length > 0 ? fromPipeline : fromReady);
    setPrs(prList);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function launchPipeline(issueNumber: number, repoSlug?: string) {
    setPipelineRunning(issueNumber);
    try {
      await runPipelineIssue(issueNumber, repoSlug);
      toast.success(`Pipeline lancé sur #${issueNumber}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur pipeline");
    } finally {
      setPipelineRunning(null);
    }
  }

  return (
    <section className="space-y-6">
      <h2 className="label-caps">Console agents App</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <AgentActionConsole
          title="Théo — Dev App"
          description="Instruction directe à l'agent Dev App (issues, PRs, coding)"
          fields={[
            {
              name: "instruction",
              label: "Instruction",
              type: "textarea",
              placeholder: "Implémente la feature X sur Naïa App…",
              required: true,
              rows: 4,
            },
          ]}
          submitLabel="Envoyer à Dev App"
          onSubmit={(v) => devAppInstruction(v.instruction)}
        />
        <AgentActionConsole
          title="Hao — Design API"
          description="Conception endpoint FastAPI + schéma"
          fields={[
            { name: "feature", label: "Feature", required: true },
            {
              name: "project",
              label: "Projet",
              defaultValue: "Naïa App",
              required: true,
            },
            {
              name: "constraints",
              label: "Contraintes",
              type: "textarea",
              rows: 2,
            },
          ]}
          onSubmit={(v) =>
            devBackendDesignApi({
              feature: v.feature,
              project: v.project,
              constraints: v.constraints,
            })
          }
        />
        <AgentActionConsole
          title="Hao — Implémenter"
          fields={[
            { name: "feature", label: "Feature", required: true },
            { name: "project", label: "Projet", defaultValue: "Naïa App", required: true },
            { name: "api_spec", label: "Spec API", type: "textarea", rows: 3 },
          ]}
          onSubmit={(v) =>
            devBackendImplement({
              feature: v.feature,
              project: v.project,
              api_spec: v.api_spec,
            })
          }
        />
        <AgentActionConsole
          title="Hao — Code Review"
          fields={[
            { name: "code", label: "Code", type: "textarea", required: true, rows: 6 },
            { name: "context", label: "Contexte", type: "textarea", rows: 2 },
          ]}
          onSubmit={(v) => devBackendReview({ code: v.code, context: v.context })}
        />
        <AgentActionConsole
          title="Hao — Debug"
          fields={[
            { name: "error", label: "Erreur", type: "textarea", required: true, rows: 2 },
            { name: "context", label: "Contexte", required: true },
            { name: "code_snippet", label: "Snippet", type: "textarea", rows: 4 },
          ]}
          onSubmit={(v) =>
            devBackendDebug({
              error: v.error,
              context: v.context,
              code_snippet: v.code_snippet,
            })
          }
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
              <GitBranch className="h-4 w-4 text-copper" />
              Issues agent-ready
            </CardTitle>
          </CardHeader>
          <CardContent>
            {issues.length === 0 ? (
              <p className="text-sm text-titanium/60">Aucune issue prête.</p>
            ) : (
              <ul className="space-y-2">
                {issues.slice(0, 8).map((issue) => (
                  <li
                    key={`${issue.repo_slug}-${issue.number}`}
                    className="flex items-center justify-between gap-2 rounded border border-copper/10 p-2 text-sm"
                  >
                    <span className="truncate text-ivory/80">
                      #{issue.number} {issue.title}
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      className="shrink-0 border-copper/30"
                      disabled={pipelineRunning === issue.number}
                      onClick={() => launchPipeline(issue.number, issue.repo_slug)}
                    >
                      {pipelineRunning === issue.number ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        "Pipeline"
                      )}
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader className="pb-2">
            <CardTitle className="font-title text-base text-ivory">Pull Requests</CardTitle>
          </CardHeader>
          <CardContent>
            {prs.length === 0 ? (
              <p className="text-sm text-titanium/60">Aucune PR ouverte.</p>
            ) : (
              <ul className="space-y-2">
                {prs.slice(0, 6).map((pr) => (
                  <li key={pr.number} className="text-sm">
                    <a
                      href={pr.html_url ?? "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-copper hover:underline"
                    >
                      #{pr.number} {pr.title}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </li>
                ))}
              </ul>
            )}
            <Button asChild size="sm" variant="ghost" className="mt-3">
              <Link href={ROUTES.hub}>Hub — pipeline complet</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
