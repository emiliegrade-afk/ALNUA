"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Rocket, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  fetchAppFactoryRun,
  startAppFactory,
  triggerFactoryPipeline,
  type AppFactoryRun,
  type FactoryStack,
} from "@/lib/app-factory-api";
import type { AppBranch } from "@/lib/apps-api";
import { toast } from "sonner";

const BRANCHES: AppBranch[] = ["app", "gaming", "robotics", "other"];

const EMPTY = {
  name: "",
  brief: "",
  stack: "nextjs" as FactoryStack,
  github_repo: "",
  local_path: "",
  branch: "app" as AppBranch,
};

const TERMINAL = new Set([
  "completed",
  "failed",
  "needs_github",
  "pipeline_failed",
]);

interface AppFactoryPanelProps {
  onRegistered?: () => void;
}

export function AppFactoryPanel({ onRegistered }: AppFactoryPanelProps) {
  const [form, setForm] = useState(EMPTY);
  const [launching, setLaunching] = useState(false);
  const [run, setRun] = useState<AppFactoryRun | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollRun = useCallback(
    (runId: string) => {
      stopPoll();
      pollRef.current = setInterval(() => {
        void fetchAppFactoryRun(runId)
          .then((data) => {
            setRun(data);
            if (TERMINAL.has(data.status)) {
              stopPoll();
              if (data.status === "completed") {
                toast.success("App factory terminée — vérifie la PR / le repo");
                onRegistered?.();
              } else if (data.status === "needs_github") {
                toast.message("Ajoute le repo GitHub dans Mes apps puis relance le pipeline");
              } else if (data.status === "failed") {
                toast.error(data.error ?? "Factory échouée");
              }
            }
          })
          .catch(() => stopPoll());
      }, 3000);
    },
    [onRegistered, stopPoll]
  );

  useEffect(() => () => stopPoll(), [stopPoll]);

  async function handleLaunch(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim() || form.brief.trim().length < 10) {
      toast.error("Nom et brief (10 car. min) requis");
      return;
    }
    setLaunching(true);
    try {
      const queued = await startAppFactory({
        name: form.name.trim(),
        brief: form.brief.trim(),
        stack: form.stack,
        github_repo: form.github_repo.trim(),
        local_path: form.local_path.trim(),
        branch: form.branch,
        auto_run_pipeline: true,
      });
      toast.success("Pôle App lancé — plan + issues en cours");
      setRun({
        run_id: queued.run_id,
        status: queued.status,
        progress: 0,
        log: ["Démarrage…"],
        slug: queued.slug,
      });
      pollRun(queued.run_id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Lancement impossible");
    } finally {
      setLaunching(false);
    }
  }

  async function handleRetryPipeline() {
    if (!run?.run_id) return;
    try {
      await triggerFactoryPipeline(run.run_id);
      toast.success("Pipeline relancé");
      pollRun(run.run_id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Pipeline impossible");
    }
  }

  return (
        <Card className="border-copper-dim/30 bg-obsidian-2/90 lg:col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
          <Rocket className="h-4 w-4 text-copper" />
          Nouvelle app — App Factory
        </CardTitle>
        <p className="label-caps">
          Brief → spec (Léon/Sam) → issues GitHub → dev_app code → PR
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <form
          className="grid gap-4 md:grid-cols-2"
          onSubmit={(e) => void handleLaunch(e)}
        >
          <div className="space-y-3 md:col-span-2">
            <div>
              <Label htmlFor="factory-name">Nom de l&apos;app</Label>
              <Input
                id="factory-name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Mon Super App"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="factory-brief">Brief / idée</Label>
              <textarea
                id="factory-brief"
                value={form.brief}
                onChange={(e) => setForm({ ...form, brief: e.target.value })}
                rows={4}
                placeholder="Décris l'app, les écrans P0, la cible utilisateur…"
                className="mt-1 w-full rounded-md border border-copper/15 bg-obsidian px-3 py-2 text-sm text-ivory"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="factory-stack">Stack</Label>
            <select
              id="factory-stack"
              value={form.stack}
              onChange={(e) =>
                setForm({ ...form, stack: e.target.value as FactoryStack })
              }
              className="mt-1 w-full rounded-md border border-copper/15 bg-obsidian px-3 py-2 text-sm text-ivory"
            >
              <option value="nextjs">Next.js (web)</option>
              <option value="expo">Expo (mobile)</option>
            </select>
          </div>
          <div>
            <Label htmlFor="factory-branch">Pôle</Label>
            <select
              id="factory-branch"
              value={form.branch}
              onChange={(e) =>
                setForm({ ...form, branch: e.target.value as AppBranch })
              }
              className="mt-1 w-full rounded-md border border-copper/15 bg-obsidian px-3 py-2 text-sm text-ivory"
            >
              {BRANCHES.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="factory-github">GitHub (owner/repo)</Label>
            <Input
              id="factory-github"
              value={form.github_repo}
              onChange={(e) =>
                setForm({ ...form, github_repo: e.target.value })
              }
              placeholder="emiliegrade-afk/mon-app"
              className="mt-1 font-mono text-xs"
            />
          </div>
          <div>
            <Label htmlFor="factory-path">Chemin local (optionnel)</Label>
            <Input
              id="factory-path"
              value={form.local_path}
              onChange={(e) =>
                setForm({ ...form, local_path: e.target.value })
              }
              placeholder="C:\Dev\mon-app"
              className="mt-1 font-mono text-xs"
            />
          </div>
          <div className="md:col-span-2">
            <Button type="submit" disabled={launching} className="w-full sm:w-auto">
              {launching ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Lancement…
                </>
              ) : (
                <>
                  <Wand2 className="mr-2 h-4 w-4" />
                  Lancer le pôle App
                </>
              )}
            </Button>
          </div>
        </form>

        {run ? (
          <div className="rounded-lg border border-copper/15 bg-obsidian/60 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-mono text-xs text-copper">
                {run.slug} · {run.status} · {run.progress}%
              </p>
              {run.status === "needs_github" ? (
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => void handleRetryPipeline()}
                >
                  Relancer pipeline
                </Button>
              ) : null}
            </div>
            <ul className="mt-3 max-h-40 space-y-1 overflow-y-auto font-mono text-[11px] text-titanium/80">
              {(run.log ?? []).map((line, i) => (
                <li key={`${i}-${line.slice(0, 24)}`}>{line}</li>
              ))}
            </ul>
            {run.issues?.length ? (
              <ul className="mt-3 space-y-1 text-xs text-titanium/70">
                {run.issues.map((iss) => (
                  <li key={iss.number}>
                    <a
                      href={iss.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-copper hover:underline"
                    >
                      #{iss.number}
                    </a>{" "}
                    {iss.title}
                  </li>
                ))}
              </ul>
            ) : null}
            {run.pipeline?.pr_url ? (
              <p className="mt-2 text-xs">
                PR:{" "}
                <a
                  href={String(run.pipeline.pr_url)}
                  target="_blank"
                  rel="noreferrer"
                  className="text-emerald-400 hover:underline"
                >
                  {String(run.pipeline.pr_url)}
                </a>
              </p>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
