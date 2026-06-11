"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { ProjectSelector } from "@/components/shared/project-selector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  fetchDevLog,
  generateRelease,
  type DevLogEntry,
} from "@/lib/releases-api";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

export type DevLogSourceMode = "last_release" | "since_date" | "pick_entries";

interface ReleaseGenerateFormProps {
  projects: Project[];
  onGenerated: (releaseId: string) => void;
}

export function ReleaseGenerateForm({
  projects,
  onGenerated,
}: ReleaseGenerateFormProps) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [version, setVersion] = useState("");
  const [sourceMode, setSourceMode] = useState<DevLogSourceMode>("last_release");
  const [sinceDate, setSinceDate] = useState("");
  const [devLogs, setDevLogs] = useState<DevLogEntry[]>([]);
  const [selectedLogIds, setSelectedLogIds] = useState<Set<string>>(new Set());
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (projects.length > 0 && !projectId) {
      setProjectId(projects[0].id);
    }
  }, [projects, projectId]);

  const loadDevLogs = useCallback(async (pid: string) => {
    if (!pid) return;
    setLoadingLogs(true);
    try {
      const entries = await fetchDevLog(pid);
      setDevLogs(entries.slice(0, 20));
      setSelectedLogIds(new Set());
    } catch {
      setDevLogs([]);
      toast.error("Impossible de charger le dev log");
    } finally {
      setLoadingLogs(false);
    }
  }, []);

  useEffect(() => {
    if (projectId && sourceMode === "pick_entries") {
      loadDevLogs(projectId);
    }
  }, [projectId, sourceMode, loadDevLogs]);

  function toggleLogId(id: string) {
    setSelectedLogIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleGenerate() {
    if (!projectId) {
      toast.error("Sélectionne un projet");
      return;
    }
    if (!version.trim()) {
      toast.error("Indique un numéro de version");
      return;
    }
    if (sourceMode === "pick_entries" && selectedLogIds.size === 0) {
      toast.error("Sélectionne au moins une entrée dev_log");
      return;
    }
    if (sourceMode === "since_date" && !sinceDate) {
      toast.error("Indique une date de début");
      return;
    }

    setGenerating(true);
    try {
      const body: Parameters<typeof generateRelease>[0] = {
        project_id: projectId,
        version: version.trim(),
      };
      if (sourceMode === "since_date") {
        body.since_date = sinceDate;
      } else if (sourceMode === "pick_entries") {
        body.dev_log_ids = Array.from(selectedLogIds);
      }

      const release = await generateRelease(body);
      toast.success(`Release v${release.version} générée`);
      onGenerated(release.id);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Échec de la génération"
      );
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="rounded-xl border border-copper/20 bg-white/[0.02] p-6">
      <div className="mb-6 flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-copper" />
        <h2 className="text-lg font-semibold text-ivory">
          Générer une nouvelle release
        </h2>
      </div>

      <div className="space-y-5">
        <div className="space-y-2">
          <Label className="text-titanium">Projet</Label>
          <ProjectSelector
            projects={projects}
            value={projectId}
            onChange={(v) => setProjectId(v)}
            mode="picker"
            triggerClassName="w-full"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="release-version" className="text-titanium">
            Version
          </Label>
          <Input
            id="release-version"
            placeholder="1.2.0"
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            className="border-copper/25 bg-white/[0.03] font-mono text-ivory"
          />
        </div>

        <fieldset className="space-y-3">
          <legend className="text-sm font-medium text-ivory/90">
            Source des entrées dev_log
          </legend>

          <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-white/10 p-3 hover:bg-white/[0.02]">
            <input
              type="radio"
              name="sourceMode"
              checked={sourceMode === "last_release"}
              onChange={() => setSourceMode("last_release")}
              className="mt-1 accent-copper"
            />
            <span>
              <span className="block text-sm text-ivory">
                Depuis la dernière release
              </span>
              <span className="text-xs text-titanium">
                Toutes les entrées depuis la release précédente
              </span>
            </span>
          </label>

          <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-white/10 p-3 hover:bg-white/[0.02]">
            <input
              type="radio"
              name="sourceMode"
              checked={sourceMode === "since_date"}
              onChange={() => setSourceMode("since_date")}
              className="mt-1 accent-copper"
            />
            <span className="flex-1">
              <span className="block text-sm text-ivory">Depuis une date</span>
              {sourceMode === "since_date" && (
                <Input
                  type="date"
                  value={sinceDate}
                  onChange={(e) => setSinceDate(e.target.value)}
                  className="mt-2 border-copper/25 bg-white/[0.03] text-ivory"
                />
              )}
            </span>
          </label>

          <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-white/10 p-3 hover:bg-white/[0.02]">
            <input
              type="radio"
              name="sourceMode"
              checked={sourceMode === "pick_entries"}
              onChange={() => setSourceMode("pick_entries")}
              className="mt-1 accent-copper"
            />
            <span className="flex-1">
              <span className="block text-sm text-ivory">
                Sélectionner les entrées dev_log
              </span>
              <span className="text-xs text-titanium">
                20 dernières entrées du projet
              </span>
            </span>
          </label>
        </fieldset>

        {sourceMode === "pick_entries" && (
          <div className="rounded-lg border border-white/10 bg-black/20">
            {loadingLogs ? (
              <div className="flex items-center justify-center py-8 text-sm text-titanium">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Chargement…
              </div>
            ) : devLogs.length === 0 ? (
              <p className="p-4 text-sm text-titanium">
                Aucune entrée dev_log pour ce projet.
              </p>
            ) : (
              <ScrollArea className="max-h-56">
                <ul className="divide-y divide-white/5">
                  {devLogs.map((entry) => (
                    <li key={entry.id}>
                      <label
                        className={cn(
                          "flex cursor-pointer gap-3 px-4 py-3 hover:bg-white/[0.02]",
                          selectedLogIds.has(entry.id) && "bg-copper/5"
                        )}
                      >
                        <input
                          type="checkbox"
                          checked={selectedLogIds.has(entry.id)}
                          onChange={() => toggleLogId(entry.id)}
                          className="mt-1 accent-copper"
                        />
                        <span className="min-w-0 flex-1">
                          <span className="font-mono text-[10px] text-titanium">
                            {entry.date}
                          </span>
                          <p className="line-clamp-2 text-sm text-ivory/90">
                            {entry.content}
                          </p>
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            )}
          </div>
        )}

        <Button
          onClick={handleGenerate}
          disabled={generating}
          className="w-full bg-copper text-obsidian hover:bg-copper-glow"
        >
          {generating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Génération en cours…
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Générer
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
