"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CONTENT_TYPES, PLATFORMS, SECTORS } from "@/components/content/content.constants";
import type { ContentSector, CreatablePostStatus, PostContentType, PostPlatform } from "@/components/content/content.constants";
import { createPost, type Post } from "@/lib/content";
import type { Project } from "@/lib/types";

/* Création manuelle de post — Phase 33, ROADMAP.md. Pas une réutilisation de
   post-composer.tsx (fige status="pending_approval" et gère la sélection
   multi-plateforme, incompatible avec un "+" par colonne du Content
   Studio) : ici le statut est pré-rempli par la colonne cliquée. */

interface ContentStudioCreateModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects: Project[];
  defaultStatus: CreatablePostStatus;
  onCreated: (post: Post) => void;
}

export function ContentStudioCreateModal({
  open,
  onOpenChange,
  projects,
  defaultStatus,
  onCreated,
}: ContentStudioCreateModalProps) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [sector, setSector] = useState<ContentSector | "none">("none");
  const [platform, setPlatform] = useState<PostPlatform>("instagram");
  const [contentType, setContentType] = useState<PostContentType>("announcement");
  const [text, setText] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    setProjectId(projects[0]?.id ?? "");
    setSector("none");
    setPlatform("instagram");
    setContentType("announcement");
    setText("");
    const now = new Date();
    setScheduledAt(new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16));
  }, [open, projects]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) {
      toast.error("Le texte est requis");
      return;
    }
    if (!projectId) {
      toast.error("Sélectionne un projet");
      return;
    }

    setSubmitting(true);
    try {
      const post = await createPost({
        project_id: projectId,
        platform,
        content_type: contentType,
        text_content: text.trim(),
        sector: sector === "none" ? undefined : sector,
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : new Date().toISOString(),
        status: defaultStatus,
      });
      toast.success("Post créé");
      onCreated(post);
      onOpenChange(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-copper/20 bg-surface-raised text-ivory/90 sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-ivory">Nouveau post</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Projet</Label>
            <Select value={projectId} onValueChange={setProjectId}>
              <SelectTrigger className="border-copper/20 bg-obsidian-deep/50">
                <SelectValue placeholder="Choisir un projet" />
              </SelectTrigger>
              <SelectContent>
                {projects.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Secteur (optionnel)</Label>
              <Select value={sector} onValueChange={(v) => setSector(v as ContentSector | "none")}>
                <SelectTrigger className="border-copper/20 bg-obsidian-deep/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Aucun</SelectItem>
                  {SECTORS.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Plateforme</Label>
              <Select value={platform} onValueChange={(v) => setPlatform(v as PostPlatform)}>
                <SelectTrigger className="border-copper/20 bg-obsidian-deep/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PLATFORMS.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Type de contenu</Label>
            <Select value={contentType} onValueChange={(v) => setContentType(v as PostContentType)}>
              <SelectTrigger className="border-copper/20 bg-obsidian-deep/50">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CONTENT_TYPES.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="studio-text">Texte</Label>
            <Textarea
              id="studio-text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={5}
              className="border-copper/20 bg-obsidian-deep/50"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="studio-schedule">Publication prévue</Label>
            <Input
              id="studio-schedule"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="border-copper/20 bg-obsidian-deep/50"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={submitting} className="bg-copper hover:bg-copper-glow">
              {submitting ? "Création…" : "Créer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
