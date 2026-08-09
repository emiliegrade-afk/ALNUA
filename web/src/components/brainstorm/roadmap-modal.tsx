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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { createRoadmapItem, type Project } from "@/lib/brainstorm";

const PRIORITY_MAP = {
  low: "low",
  medium: "medium",
  high: "high",
} as const;

interface RoadmapModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultTitle: string;
  defaultDescription: string;
  defaultProjectId: string | null;
  projects: Project[];
}

export function RoadmapModal({
  open,
  onOpenChange,
  defaultTitle,
  defaultDescription,
  defaultProjectId,
  projects,
}: RoadmapModalProps) {
  const [title, setTitle] = useState(defaultTitle);
  const [description, setDescription] = useState(defaultDescription);
  const [projectId, setProjectId] = useState(
    defaultProjectId ?? projects[0]?.id ?? ""
  );
  const [priority, setPriority] = useState<"low" | "medium" | "high">("medium");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setTitle(defaultTitle);
      setDescription(defaultDescription);
      setProjectId(defaultProjectId ?? projects[0]?.id ?? "");
      setPriority("medium");
    }
  }, [open, defaultTitle, defaultDescription, defaultProjectId, projects]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !projectId) {
      toast.error("Titre et projet requis");
      return;
    }

    setSubmitting(true);
    try {
      await createRoadmapItem({
        project_id: projectId,
        title: title.trim(),
        description: description.trim(),
        priority: PRIORITY_MAP[priority],
      });
      toast.success("Ajouté à la roadmap");
      onOpenChange(false);
    } catch {
      toast.error("Erreur lors de la création");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-copper/15 bg-surface-raised text-ivory/90 sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-ivory">Convertir en roadmap</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="rm-title">Titre</Label>
            <Input
              id="rm-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="border-copper/15 bg-obsidian-deep/50"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="rm-desc">Description</Label>
            <Textarea
              id="rm-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="border-copper/15 bg-obsidian-deep/50"
            />
          </div>
          <div className="space-y-2">
            <Label>Projet</Label>
            <Select value={projectId} onValueChange={setProjectId}>
              <SelectTrigger className="border-copper/15 bg-obsidian-deep/50">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-copper/15 bg-surface-raised">
                {projects.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Priorité</Label>
            <Select
              value={priority}
              onValueChange={(v) => setPriority(v as typeof priority)}
            >
              <SelectTrigger className="border-copper/15 bg-obsidian-deep/50">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-copper/15 bg-surface-raised">
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
              className="text-titanium/80"
            >
              Annuler
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="bg-copper hover:bg-copper"
            >
              {submitting ? "Enregistrement…" : "Confirmer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
