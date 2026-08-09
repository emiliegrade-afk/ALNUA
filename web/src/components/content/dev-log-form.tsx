"use client";

import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  CONTENT_TYPES,
  GLOBAL_PROJECT_ID,
  PLATFORMS,
} from "@/components/content/content.constants";
import { ProjectSelector } from "@/components/shared/project-selector";
import { generatePosts } from "@/lib/content";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface DevLogFormProps {
  projects: Project[];
  onGenerated: () => void;
  onProjectsUpdated?: (projects: Project[]) => void;
}

function ToggleChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-lg border px-2.5 py-1.5 text-left text-[11px] transition",
        active
          ? "border-copper/40 bg-copper/15 text-copper-glow"
          : "border-copper/15 bg-obsidian-deep/40 text-titanium hover:border-copper/20"
      )}
    >
      {label}
    </button>
  );
}

export function DevLogForm({ projects, onGenerated, onProjectsUpdated }: DevLogFormProps) {
  const [projectScope, setProjectScope] = useState<string>(
    projects[0]?.id ?? GLOBAL_PROJECT_ID
  );
  const [devLog, setDevLog] = useState("");
  const [contentTypes, setContentTypes] = useState<string[]>(["announcement"]);
  const [platforms, setPlatforms] = useState<string[]>(["instagram", "x"]);
  const [loading, setLoading] = useState(false);

  function toggleItem(list: string[], id: string, setter: (v: string[]) => void) {
    setter(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
  }

  async function handleGenerate() {
    if (!devLog.trim()) {
      toast.error("Décris ce que tu as buildé");
      return;
    }
    if (!contentTypes.length || !platforms.length) {
      toast.error("Sélectionne au moins un type et une plateforme");
      return;
    }

    const isGlobal = projectScope === GLOBAL_PROJECT_ID;
    const projectId = isGlobal ? projects[0]?.id : projectScope;
    if (!projectId) {
      toast.error("Aucun projet disponible");
      return;
    }

    setLoading(true);
    try {
      const result = await generatePosts({
        project_id: projectId,
        dev_log: devLog.trim(),
        content_types: contentTypes,
        platforms,
        alnua_global: isGlobal,
      });
      toast.success(`${result.posts_created} post(s) généré(s)`);
      setDevLog("");
      onGenerated();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Erreur lors de la génération"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="border-copper/15 bg-surface/80 ring-1 ring-copper/10">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-copper" />
          <CardTitle className="text-base text-ivory">
            Qu&apos;est-ce que tu as buildé ?
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <ProjectSelector
          projects={projects}
          value={projectScope}
          onChange={(value) => setProjectScope(value)}
          onProjectsUpdated={onProjectsUpdated}
          mode="content"
        />

        <Textarea
          value={devLog}
          onChange={(e) => setDevLog(e.target.value)}
          placeholder="Décris ce que tu as fait aujourd'hui ou cette semaine…"
          rows={5}
          disabled={loading}
          className="border-copper/15 bg-obsidian-deep/40 text-ivory/90 placeholder:text-titanium/60"
        />

        <div>
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-titanium">
            Types de contenu
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {CONTENT_TYPES.map(({ id, label }) => (
              <ToggleChip
                key={id}
                label={label}
                active={contentTypes.includes(id)}
                onClick={() => toggleItem(contentTypes, id, setContentTypes)}
              />
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-titanium">
            Plateformes
          </p>
          <div className="flex flex-wrap gap-1.5">
            {PLATFORMS.map(({ id, label }) => (
              <ToggleChip
                key={id}
                label={label}
                active={platforms.includes(id)}
                onClick={() => toggleItem(platforms, id, setPlatforms)}
              />
            ))}
          </div>
        </div>

        <Button
          onClick={handleGenerate}
          disabled={loading}
          className="w-full bg-copper hover:bg-copper-glow"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              L&apos;agent crée tes posts…
            </>
          ) : (
            "Générer les posts"
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
