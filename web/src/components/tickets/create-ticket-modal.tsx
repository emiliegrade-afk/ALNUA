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
  TICKET_PRIORITIES,
  TICKET_TYPES,
  type TicketPriority,
  type TicketType,
} from "@/components/tickets/tickets.constants";
import { ProjectSelector } from "@/components/shared/project-selector";
import { createTicket, type TicketWithProject } from "@/lib/tickets";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { Project } from "@/lib/types";

const UNASSIGNED = "__unassigned__";

interface CreateTicketModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects: Project[];
  defaultProjectId?: string;
  onCreated: (ticket: TicketWithProject) => void;
  onProjectsUpdated?: (projects: Project[]) => void;
  agents?: BureauAgentDef[];
}

export function CreateTicketModal({
  open,
  onOpenChange,
  projects,
  defaultProjectId,
  onCreated,
  onProjectsUpdated,
  agents = [],
}: CreateTicketModalProps) {
  const [title, setTitle] = useState("");
  const [type, setType] = useState<TicketType>("bug");
  const [priority, setPriority] = useState<TicketPriority>("medium");
  const [projectId, setProjectId] = useState(
    defaultProjectId ?? projects[0]?.id ?? ""
  );
  const [description, setDescription] = useState("");
  const [assigneeId, setAssigneeId] = useState(UNASSIGNED);
  const [storyPoints, setStoryPoints] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setTitle("");
      setDescription("");
      setType("bug");
      setPriority("medium");
      setProjectId(defaultProjectId ?? projects[0]?.id ?? "");
      setAssigneeId(UNASSIGNED);
      setStoryPoints("");
      setDueDate("");
    }
  }, [open, defaultProjectId, projects]);

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

    const points = Number(storyPoints);
    setSubmitting(true);
    try {
      const ticket = await createTicket({
        title: title.trim(),
        type,
        priority,
        project_id: projectId,
        description: description.trim(),
        ...(assigneeId !== UNASSIGNED ? { assignee_agent_id: assigneeId } : {}),
        ...(storyPoints.trim() && Number.isFinite(points) ? { story_points: points } : {}),
        ...(dueDate ? { due_date: dueDate } : {}),
      });
      toast.success("Ticket créé");
      onCreated(ticket);
      onOpenChange(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur création");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-copper/20 bg-surface-raised sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-ivory">Nouveau ticket</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ticket-title">Titre *</Label>
            <Input
              id="ticket-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={submitting}
              className="border-copper/20 bg-obsidian text-ivory"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select
                value={type}
                onValueChange={(v) => setType(v as TicketType)}
                disabled={submitting}
              >
                <SelectTrigger className="border-copper/20 bg-obsidian">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-copper/20 bg-surface-raised">
                  {TICKET_TYPES.map(({ id, label }) => (
                    <SelectItem key={id} value={id}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Priorité</Label>
              <Select
                value={priority}
                onValueChange={(v) => setPriority(v as TicketPriority)}
                disabled={submitting}
              >
                <SelectTrigger className="border-copper/20 bg-obsidian">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-copper/20 bg-surface-raised">
                  {TICKET_PRIORITIES.map(({ id, label }) => (
                    <SelectItem key={id} value={id}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Projet</Label>
            <ProjectSelector
              projects={projects}
              value={projectId}
              onChange={(value) => setProjectId(value)}
              onProjectsUpdated={onProjectsUpdated}
              mode="picker"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Assigné</Label>
              <Select value={assigneeId} onValueChange={setAssigneeId} disabled={submitting || agents.length === 0}>
                <SelectTrigger className="border-copper/20 bg-obsidian">
                  <SelectValue placeholder="Non assigné" />
                </SelectTrigger>
                <SelectContent className="border-copper/20 bg-surface-raised">
                  <SelectItem value={UNASSIGNED}>Non assigné</SelectItem>
                  {agents.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="ticket-points">Points</Label>
              <Input
                id="ticket-points"
                type="number"
                min={1}
                max={21}
                value={storyPoints}
                onChange={(e) => setStoryPoints(e.target.value)}
                disabled={submitting}
                placeholder="—"
                className="border-copper/20 bg-obsidian text-ivory"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="ticket-due">Échéance</Label>
            <Input
              id="ticket-due"
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              disabled={submitting}
              className="border-copper/20 bg-obsidian text-ivory"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ticket-desc">Description</Label>
            <Textarea
              id="ticket-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={5}
              disabled={submitting}
              placeholder="Décris le bug, la feature ou le contexte (markdown supporté)…"
              className="border-copper/20 bg-obsidian text-ivory resize-none"
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
              className="border-white/10"
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
                "Créer"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
