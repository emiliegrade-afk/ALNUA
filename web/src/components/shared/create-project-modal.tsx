"use client";

import { useState } from "react";
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
import { createProject } from "@/lib/api";
import type { Project, ProjectBranch } from "@/lib/types";
import { cn } from "@/lib/utils";

const BRANCH_OPTIONS: {
  id: ProjectBranch;
  label: string;
  dotClass: string;
}[] = [
  { id: "app", label: "App", dotClass: "bg-naia" },
  { id: "gaming", label: "Gaming", dotClass: "bg-wyrdheim" },
  { id: "robotics", label: "Robotique", dotClass: "bg-eve" },
  { id: "other", label: "Autre", dotClass: "bg-violet-500" },
];

interface CreateProjectModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: (project: Project) => void;
}

export function CreateProjectModal({
  open,
  onOpenChange,
  onCreated,
}: CreateProjectModalProps) {
  const [name, setName] = useState("");
  const [branch, setBranch] = useState<ProjectBranch>("app");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Le nom du projet est requis");
      return;
    }

    setSubmitting(true);
    try {
      const project = await createProject({
        name: name.trim(),
        branch,
        description: description.trim(),
        status: "dev",
      });
      toast.success(`Projet « ${project.name} » créé`);
      onCreated(project);
      onOpenChange(false);
      setName("");
      setDescription("");
      setBranch("app");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Impossible de créer le projet"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-copper/20 bg-surface-raised text-ivory sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-ivory">
            Créer un projet ALNUA
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="project-name" className="text-titanium">
              Nom du projet *
            </Label>
            <Input
              id="project-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Mon nouveau projet"
              disabled={submitting}
              className="border-copper/20 bg-white/[0.03] text-ivory"
            />
          </div>

          <fieldset className="space-y-2">
            <legend className="text-sm text-titanium">Branche *</legend>
            <div className="grid grid-cols-2 gap-2">
              {BRANCH_OPTIONS.map((opt) => (
                <label
                  key={opt.id}
                  className={cn(
                    "flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition",
                    branch === opt.id
                      ? "border-copper/40 bg-copper/10 text-ivory"
                      : "border-white/[0.08] text-titanium hover:border-copper/20"
                  )}
                >
                  <input
                    type="radio"
                    name="branch"
                    value={opt.id}
                    checked={branch === opt.id}
                    onChange={() => setBranch(opt.id)}
                    className="sr-only"
                  />
                  <span className={cn("h-2 w-2 rounded-full", opt.dotClass)} />
                  {opt.label}
                </label>
              ))}
            </div>
          </fieldset>

          <div className="space-y-2">
            <Label htmlFor="project-desc" className="text-titanium">
              Description courte
            </Label>
            <Textarea
              id="project-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              disabled={submitting}
              placeholder="En une phrase, de quoi il s'agit…"
              className="border-copper/20 bg-white/[0.03] text-ivory resize-none"
            />
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
              className="border-white/10 text-titanium"
            >
              Annuler
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="bg-copper hover:bg-copper-glow"
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Création…
                </>
              ) : (
                "Créer le projet"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
