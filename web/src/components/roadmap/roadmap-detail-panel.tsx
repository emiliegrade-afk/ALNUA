"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  ExternalLink,
  Loader2,
  Pencil,
  Trash2,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  normalizePriority,
  normalizeStatus,
  ROADMAP_PRIORITIES,
  ROADMAP_STATUSES,
  STATUS_STYLES,
} from "@/components/roadmap/roadmap.constants";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { deleteRoadmapItem, updateRoadmapItem } from "@/lib/roadmap";
import { getProjectAccent } from "@/lib/projects";
import type {
  RoadmapItem,
  RoadmapPriority,
  RoadmapStatus,
} from "@/lib/types";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface RoadmapDetailPanelProps {
  item: RoadmapItem | null;
  projects: Project[];
  open: boolean;
  onClose: () => void;
  onUpdated: (item: RoadmapItem) => void;
  onDeleted: (id: string) => void;
}

export function RoadmapDetailPanel({
  item,
  projects,
  open,
  onClose,
  onUpdated,
  onDeleted,
}: RoadmapDetailPanelProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [phase, setPhase] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [editingTitle, setEditingTitle] = useState(false);
  const [editingDescription, setEditingDescription] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (item) {
      setTitle(item.title);
      setDescription(item.description ?? "");
      setPhase(item.phase ?? "");
      setDueDate(item.due_date?.slice(0, 10) ?? "");
      setEditingTitle(false);
      setEditingDescription(false);
      setConfirmDelete(false);
    }
  }, [item]);

  if (!open || !item) return null;

  const status = normalizeStatus(item.status);
  const priority = normalizePriority(item.priority);
  const project = projects.find((p) => p.id === item.project_id);
  const accent = project ? getProjectAccent(project.branch) : null;

  async function patch(
    data: Parameters<typeof updateRoadmapItem>[1],
    successMsg: string
  ) {
    if (!item) return;
    setSaving(true);
    try {
      const updated = await updateRoadmapItem(item.id, data);
      onUpdated(updated);
      toast.success(successMsg);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  async function saveTitle() {
    if (!item || title.trim() === item.title) {
      setEditingTitle(false);
      return;
    }
    await patch({ title: title.trim() }, "Titre enregistré");
    setEditingTitle(false);
  }

  async function saveDescription() {
    if (!item || description === (item.description ?? "")) {
      setEditingDescription(false);
      return;
    }
    await patch({ description: description.trim() }, "Description enregistrée");
    setEditingDescription(false);
  }

  async function handleDelete() {
    if (!item) return;
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setSaving(true);
    try {
      await deleteRoadmapItem(item.id);
      onDeleted(item.id);
      onClose();
      toast.success("Item supprimé");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
      setConfirmDelete(false);
    }
  }

  return (
    <>
      <button
        type="button"
        aria-label="Fermer le panneau"
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[480px] flex-col border-l border-copper/15 bg-surface-raised shadow-2xl">
        <div className="shrink-0 border-b border-white/[0.06] p-4">
          <div className="mb-3 flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              {editingTitle ? (
                <div className="space-y-2">
                  <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    disabled={saving}
                    className="w-full rounded border border-copper/30 bg-obsidian px-2 py-1.5 text-lg font-semibold text-ivory outline-none focus:ring-1 focus:ring-copper/40"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={saveTitle} disabled={saving}>
                      Enregistrer
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setTitle(item.title);
                        setEditingTitle(false);
                      }}
                    >
                      Annuler
                    </Button>
                  </div>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setEditingTitle(true)}
                  className="group flex items-start gap-2 text-left"
                >
                  <h2 className="text-lg font-semibold text-ivory group-hover:text-copper-glow">
                    {item.title}
                  </h2>
                  <Pencil className="mt-1 h-3.5 w-3.5 shrink-0 text-titanium opacity-0 transition group-hover:opacity-100" />
                </button>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded p-1.5 text-titanium hover:bg-white/[0.05] hover:text-ivory"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {project && accent && (
              <Badge
                variant="outline"
                className={cn(accent.bg, accent.border, accent.color)}
              >
                {project.name}
              </Badge>
            )}
            <Badge
              variant="outline"
              className={STATUS_STYLES[status]}
            >
              {ROADMAP_STATUSES.find((s) => s.id === status)?.label}
            </Badge>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-5">
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-wider text-titanium/60">
                Status
              </label>
              <div className="flex flex-wrap gap-1.5">
                {ROADMAP_STATUSES.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    disabled={saving}
                    onClick={() =>
                      s.id !== status &&
                      patch({ status: s.id as RoadmapStatus }, "Status mis à jour")
                    }
                    className={cn(
                      "rounded-lg border px-2.5 py-1 text-xs transition",
                      status === s.id
                        ? STATUS_STYLES[s.id]
                        : "border-white/[0.08] text-titanium hover:border-copper/20"
                    )}
                  >
                    {s.emoji} {s.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <label className="text-[10px] uppercase tracking-wider text-titanium/60">
                  Priorité
                </label>
                <Select
                  value={priority}
                  onValueChange={(v) =>
                    patch({ priority: v as RoadmapPriority }, "Priorité mise à jour")
                  }
                  disabled={saving}
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

              <div className="space-y-2">
                <label className="text-[10px] uppercase tracking-wider text-titanium/60">
                  Projet
                </label>
                <Select
                  value={item.project_id}
                  onValueChange={(v) =>
                    patch({ project_id: v }, "Projet mis à jour")
                  }
                  disabled={saving}
                >
                  <SelectTrigger className="border-copper/20 bg-obsidian">
                    <SelectValue />
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
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <label
                  htmlFor="detail-phase"
                  className="text-[10px] uppercase tracking-wider text-titanium/60"
                >
                  Phase
                </label>
                <input
                  id="detail-phase"
                  value={phase}
                  onChange={(e) => setPhase(e.target.value)}
                  onBlur={() => {
                    if (phase !== (item.phase ?? "")) {
                      patch({ phase: phase.trim() || "" }, "Phase enregistrée");
                    }
                  }}
                  disabled={saving}
                  className="w-full rounded border border-copper/20 bg-obsidian px-2 py-1.5 text-sm text-ivory"
                  placeholder="v1.0, Beta…"
                />
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="detail-due"
                  className="text-[10px] uppercase tracking-wider text-titanium/60"
                >
                  Date limite
                </label>
                <input
                  id="detail-due"
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  onBlur={() => {
                    const current = item.due_date?.slice(0, 10) ?? "";
                    if (dueDate !== current) {
                      patch(
                        { due_date: dueDate || null },
                        "Date limite enregistrée"
                      );
                    }
                  }}
                  disabled={saving}
                  className="w-full rounded border border-copper/20 bg-obsidian px-2 py-1.5 text-sm text-ivory"
                />
              </div>
            </div>

            {item.linked_ticket_id && (
              <Link
                href={`/tickets`}
                className="inline-flex items-center gap-2 rounded-lg border border-copper/25 bg-copper/10 px-3 py-2 text-sm text-copper-glow transition hover:bg-copper/15"
              >
                <ExternalLink className="h-4 w-4" />
                Voir le ticket
              </Link>
            )}

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-[10px] uppercase tracking-wider text-titanium/60">
                  Description
                </label>
                {!editingDescription && (
                  <button
                    type="button"
                    onClick={() => setEditingDescription(true)}
                    className="text-[11px] text-copper/80 hover:text-copper-glow"
                  >
                    Modifier
                  </button>
                )}
              </div>
              {editingDescription ? (
                <div className="space-y-2">
                  <Textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={6}
                    className="border-copper/20 bg-obsidian font-mono text-sm"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={saveDescription} disabled={saving}>
                      Enregistrer
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setDescription(item.description ?? "");
                        setEditingDescription(false);
                      }}
                    >
                      Annuler
                    </Button>
                  </div>
                </div>
              ) : (
                <MarkdownContent>{description}</MarkdownContent>
              )}
            </div>

            <p className="text-[11px] text-titanium/50">
              Créé le{" "}
              {format(new Date(item.created_at), "d MMM yyyy à HH:mm", {
                locale: fr,
              })}
            </p>
          </div>
        </ScrollArea>

        <div className="shrink-0 border-t border-white/[0.06] p-4">
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1 border-copper/20"
              onClick={onClose}
            >
              Fermer
            </Button>
            <Button
              variant="outline"
              onClick={handleDelete}
              disabled={saving}
              className={cn(
                "border-red-500/30 text-red-400 hover:bg-red-500/10",
                confirmDelete && "bg-red-500/15"
              )}
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Trash2 className="mr-2 h-4 w-4" />
                  {confirmDelete ? "Confirmer ?" : "Supprimer"}
                </>
              )}
            </Button>
          </div>
        </div>
      </aside>
    </>
  );
}
