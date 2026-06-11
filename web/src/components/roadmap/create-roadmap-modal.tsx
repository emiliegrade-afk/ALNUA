"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
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
import {
  ROADMAP_PRIORITIES,
  ROADMAP_STATUSES,
} from "@/components/roadmap/roadmap.constants";
import { createRoadmapItem } from "@/lib/roadmap";
import type { RoadmapItem, RoadmapPriority, RoadmapStatus } from "@/lib/types";
import type { Project } from "@/lib/types";

interface CreateRoadmapModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects: Project[];
  defaultProjectId?: string;
  defaultStatus?: RoadmapStatus;
  onCreated: (item: RoadmapItem) => void;
}

export function CreateRoadmapModal({
  open,
  onOpenChange,
  projects,
  defaultProjectId,
  defaultStatus = "planned",
  onCreated,
}: CreateRoadmapModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<RoadmapStatus>(defaultStatus);
  const [priority, setPriority] = useState<RoadmapPriority>("medium");
  const [projectId, setProjectId] = useState(
    defaultProjectId ?? projects[0]?.id ?? ""
  );
  const [phase, setPhase] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setTitle("");
      setDescription("");
      setStatus(defaultStatus);
      setPriority("medium");
      setProjectId(defaultProjectId ?? projects[0]?.id ?? "");
      setPhase("");
      setDueDate("");
    }
  }, [open, defaultProjectId, defaultStatus, projects]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      toast.error("Le titre est requis");
      return;
    }
    if (!projectId) {
      toast.error("Sélectionne un projet");
      return;
    }

    setSubmitting(true);
    try {
      const item = await createRoadmapItem({
        title: title.trim(),
        description: description.trim(),
        status,
        priority,
        project_id: projectId,
        phase: phase.trim() || undefined,
        due_date: dueDate || undefined,
      });
      onCreated(item);
      onOpenChange(false);
      toast.success("Item créé");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-copper/20 bg-surface-raised sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-ivory">Nouvel item roadmap</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="roadmap-title">Titre *</Label>
            <Input
              id="roadmap-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Feature, jalon, milestone…"
              className="border-copper/20 bg-obsidian"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="roadmap-desc">Description</Label>
            <Textarea
              id="roadmap-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="border-copper/20 bg-obsidian"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={status}
                onValueChange={(v) => setStatus(v as RoadmapStatus)}
              >
                <SelectTrigger className="border-copper/20 bg-obsidian">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-copper/20 bg-surface-raised">
                  {ROADMAP_STATUSES.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.emoji} {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Priorité</Label>
              <Select
                value={priority}
                onValueChange={(v) => setPriority(v as RoadmapPriority)}
              >
                <SelectTrigger className="border-copper/20 bg-obsidian">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-copper/20 bg-surface-raised">
                  {ROADMAP_PRIORITIES.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Projet</Label>
            <Select value={projectId} onValueChange={setProjectId}>
              <SelectTrigger className="border-copper/20 bg-obsidian">
                <SelectValue placeholder="Choisir un projet" />
              </SelectTrigger>
              <SelectContent className="border-copper/20 bg-surface-raised">
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
              <Label htmlFor="roadmap-phase">Phase</Label>
              <Input
                id="roadmap-phase"
                value={phase}
                onChange={(e) => setPhase(e.target.value)}
                placeholder="v1.0, Beta…"
                className="border-copper/20 bg-obsidian"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="roadmap-due">Date limite</Label>
              <Input
                id="roadmap-due"
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="border-copper/20 bg-obsidian"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Annuler
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="bg-copper hover:bg-copper-glow"
            >
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Créer
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
