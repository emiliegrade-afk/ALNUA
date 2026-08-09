"use client";

import { useState } from "react";
import { Loader2, Send } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  GLOBAL_PROJECT_ID,
  PLATFORMS,
  SECTORS,
  type ContentSector,
} from "@/components/content/content.constants";
import { ProjectSelector } from "@/components/shared/project-selector";
import { createPost, type Post } from "@/lib/content";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

const SECTOR_AUTHOR_AGENT: Record<ContentSector, string> = {
  app: "content_app",
  gaming: "content_gaming",
  robo: "content_robo",
  company: "content_company",
};

function Chip({
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

interface PostComposerProps {
  projects: Project[];
  onProjectsUpdated?: (projects: Project[]) => void;
  onCreated: (posts: Post[]) => void;
}

export function PostComposer({ projects, onProjectsUpdated, onCreated }: PostComposerProps) {
  const [sector, setSector] = useState<ContentSector>("app");
  const [projectScope, setProjectScope] = useState<string>(
    projects[0]?.id ?? GLOBAL_PROJECT_ID
  );
  const [platforms, setPlatforms] = useState<string[]>(["instagram"]);
  const [text, setText] = useState("");
  const [hook, setHook] = useState("");
  const [cta, setCta] = useState("");
  const [hashtags, setHashtags] = useState("");
  const [channel, setChannel] = useState("dev-log");
  const [scheduledAt, setScheduledAt] = useState("");
  const [loading, setLoading] = useState(false);

  function togglePlatform(id: string) {
    setPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  }

  async function handleSubmit() {
    if (!text.trim()) {
      toast.error("Écris le contenu du post");
      return;
    }
    if (!platforms.length) {
      toast.error("Sélectionne au moins une plateforme");
      return;
    }

    const isGlobal = projectScope === GLOBAL_PROJECT_ID;
    const projectId = isGlobal ? projects[0]?.id : projectScope;
    if (!projectId) {
      toast.error("Aucun projet disponible");
      return;
    }

    const tagList = hashtags
      .split(/[\s,#]+/)
      .map((t) => t.replace(/^#/, "").trim())
      .filter(Boolean);
    const layout = hook.trim() || cta.trim() ? { hook: hook.trim(), cta: cta.trim() } : undefined;
    const scheduledIso = scheduledAt
      ? new Date(scheduledAt).toISOString()
      : new Date(Date.now() + 60 * 60 * 1000).toISOString();

    setLoading(true);
    try {
      const created = await Promise.all(
        platforms.map((platform) =>
          createPost({
            project_id: projectId,
            platform,
            content_type: "announcement",
            text_content: text.trim(),
            sector,
            author_agent_id: SECTOR_AUTHOR_AGENT[sector],
            hashtags: tagList,
            layout,
            channel: platform === "discord" ? channel.trim() || "dev-log" : undefined,
            scheduled_at: scheduledIso,
            status: "pending_approval",
          })
        )
      );
      toast.success(`${created.length} post(s) créé(s) — en attente d'approbation`);
      onCreated(created);
      setText("");
      setHook("");
      setCta("");
      setHashtags("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de la création");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="border-copper/15 bg-surface/80 ring-1 ring-copper/10">
      <CardHeader className="pb-3">
        <CardTitle className="text-base text-ivory">Composer</CardTitle>
        <p className="text-xs text-titanium">
          Écris un post et mets-le en queue, avec mise en page par plateforme.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-titanium">
            Secteur
          </p>
          <div className="flex flex-wrap gap-1.5">
            {SECTORS.map(({ id, label, agent }) => (
              <Chip
                key={id}
                label={`${label} · ${agent}`}
                active={sector === id}
                onClick={() => setSector(id)}
              />
            ))}
          </div>
        </div>

        <ProjectSelector
          projects={projects}
          value={projectScope}
          onChange={(value) => setProjectScope(value)}
          onProjectsUpdated={onProjectsUpdated}
          mode="content"
        />

        <div>
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-titanium">
            Plateformes (un post par plateforme sélectionnée)
          </p>
          <div className="flex flex-wrap gap-1.5">
            {PLATFORMS.map(({ id, label }) => (
              <Chip
                key={id}
                label={label}
                active={platforms.includes(id)}
                onClick={() => togglePlatform(id)}
              />
            ))}
          </div>
        </div>

        {platforms.includes("discord") && (
          <div className="space-y-2">
            <Label htmlFor="composer-channel">Channel Discord</Label>
            <Input
              id="composer-channel"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              placeholder="dev-log"
              className="border-copper/15 bg-obsidian-deep/40"
            />
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="composer-hook">Hook (optionnel)</Label>
            <Input
              id="composer-hook"
              value={hook}
              onChange={(e) => setHook(e.target.value)}
              placeholder="1ère ligne qui accroche"
              className="border-copper/15 bg-obsidian-deep/40"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="composer-cta">CTA (optionnel)</Label>
            <Input
              id="composer-cta"
              value={cta}
              onChange={(e) => setCta(e.target.value)}
              placeholder="Découvrir, wishlist, DM ouverts…"
              className="border-copper/15 bg-obsidian-deep/40"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="composer-text">Contenu</Label>
          <Textarea
            id="composer-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={6}
            placeholder="Le texte du post…"
            className="border-copper/15 bg-obsidian-deep/40 text-ivory/90 placeholder:text-titanium/60"
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="composer-tags">Hashtags</Label>
            <Input
              id="composer-tags"
              value={hashtags}
              onChange={(e) => setHashtags(e.target.value)}
              placeholder="#ALNUA #buildinpublic"
              className="border-copper/15 bg-obsidian-deep/40"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="composer-schedule">Publication prévue</Label>
            <Input
              id="composer-schedule"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="border-copper/15 bg-obsidian-deep/40"
            />
          </div>
        </div>

        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-copper hover:bg-copper-glow"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Mise en queue…
            </>
          ) : (
            <>
              <Send className="mr-2 h-4 w-4" />
              Mettre en queue ({platforms.length || 0} plateforme
              {platforms.length > 1 ? "s" : ""})
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
