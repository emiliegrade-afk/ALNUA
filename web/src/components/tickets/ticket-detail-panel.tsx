"use client";

import { useEffect, useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  CheckCircle2,
  Copy,
  Loader2,
  Map,
  Pencil,
  PlayCircle,
  RotateCcw,
  X,
  Zap,
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
  SOURCE_LABELS,
  TICKET_PRIORITIES,
  TICKET_STATUSES,
  TYPE_STYLES,
  type TicketPriority,
  type TicketSource,
  type TicketStatus,
  type TicketType,
} from "@/components/tickets/tickets.constants";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { getProjectAccent } from "@/lib/projects";
import {
  createRoadmapFromTicket,
  generateCursorPrompt,
  updateTicket,
  type TicketWithProject,
} from "@/lib/tickets";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface TicketDetailPanelProps {
  ticket: TicketWithProject | null;
  project?: Project;
  open: boolean;
  onClose: () => void;
  onUpdated: (ticket: TicketWithProject) => void;
  onResolved?: () => void;
}

export function TicketDetailPanel({
  ticket,
  project,
  open,
  onClose,
  onUpdated,
  onResolved,
}: TicketDetailPanelProps) {
  const [editingTitle, setEditingTitle] = useState(false);
  const [editingDescription, setEditingDescription] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (ticket) {
      setTitle(ticket.title);
      setDescription(ticket.description ?? "");
      setEditingTitle(false);
      setEditingDescription(false);
    }
  }, [ticket]);

  if (!open || !ticket) return null;

  const type = ticket.type as TicketType;
  const priority = ticket.priority as TicketPriority;
  const status = ticket.status as TicketStatus;
  const source = ticket.source as TicketSource;
  const accent = project ? getProjectAccent(project.branch) : null;
  const isClosed = status === "done" || status === "wont_fix";

  async function saveTitle() {
    if (!ticket || title.trim() === ticket.title) {
      setEditingTitle(false);
      return;
    }
    setSaving(true);
    try {
      const updated = await updateTicket(ticket.id, { title: title.trim() });
      onUpdated(updated);
      setEditingTitle(false);
      toast.success("Titre enregistré");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  async function saveDescription() {
    if (!ticket || description === (ticket.description ?? "")) {
      setEditingDescription(false);
      return;
    }
    setSaving(true);
    try {
      const updated = await updateTicket(ticket.id, {
        description: description.trim(),
      });
      onUpdated(updated);
      setEditingDescription(false);
      toast.success("Description enregistrée");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  async function setStatus(next: TicketStatus, successMsg: string) {
    if (!ticket || next === ticket.status) return;
    setSaving(true);
    try {
      const updated = await updateTicket(ticket.id, { status: next });
      onUpdated(updated);
      toast.success(successMsg);
      if (next === "done" || next === "wont_fix") {
        onResolved?.();
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Impossible de mettre à jour");
    } finally {
      setSaving(false);
    }
  }

  async function handlePriorityChange(next: TicketPriority) {
    if (!ticket || next === ticket.priority) return;
    setSaving(true);
    try {
      const updated = await updateTicket(ticket.id, { priority: next });
      onUpdated(updated);
      toast.success("Priorité mise à jour");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  async function handleGeneratePrompt() {
    if (!ticket) return;
    setGenerating(true);
    try {
      const result = await generateCursorPrompt(ticket.id);
      onUpdated(result.ticket);
      toast.success("Prompt Cursor prêt — copie-le dans Composer");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur Spec Agent");
    } finally {
      setGenerating(false);
    }
  }

  async function handleCopyPrompt() {
    if (!ticket?.cursor_prompt) return;
    try {
      await navigator.clipboard.writeText(ticket.cursor_prompt);
      toast.success("Prompt copié — colle-le dans Cursor (Ctrl+V)");
    } catch {
      toast.error("Impossible de copier");
    }
  }

  async function handleCreateRoadmap() {
    if (!ticket) return;
    try {
      await createRoadmapFromTicket(ticket.id);
      toast.success("Ajouté à la roadmap");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur roadmap");
    }
  }

  return (
    <>
      <button
        type="button"
        aria-label="Fermer le panneau"
        className="fixed inset-0 z-40 bg-obsidian/85 backdrop-blur-sm"
        onClick={onClose}
      />

      <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[480px] flex-col border-l border-copper/15 bg-surface-raised shadow-2xl">
        {/* En-tête */}
        <div className="shrink-0 border-b border-copper/10 p-4">
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
                        setTitle(ticket.title);
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
                    {ticket.title}
                  </h2>
                  <Pencil className="mt-1 h-3.5 w-3.5 shrink-0 text-titanium opacity-0 transition group-hover:opacity-100" />
                </button>
              )}
              <p className="mt-1 text-[11px] text-titanium/60">
                Clique sur le titre ou la description pour les modifier
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              title="Fermer le panneau (le ticket reste ouvert)"
              className="rounded p-1.5 text-titanium hover:bg-obsidian-deep/50 hover:text-ivory"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Actions principales — toujours visibles */}
          <div className="flex flex-wrap gap-2">
            {status === "open" && (
              <Button
                size="sm"
                variant="outline"
                disabled={saving}
                onClick={() => setStatus("in_progress", "Ticket pris en charge")}
                className="border-blue-500/30 text-blue-300 hover:bg-blue-500/10"
              >
                <PlayCircle className="mr-1.5 h-4 w-4" />
                Prendre en charge
              </Button>
            )}
            {!isClosed && (
              <Button
                size="sm"
                disabled={saving}
                onClick={() => setStatus("done", "Ticket marqué comme résolu ✓")}
                className="bg-emerald-600 hover:bg-emerald-500"
              >
                <CheckCircle2 className="mr-1.5 h-4 w-4" />
                Marquer résolu
              </Button>
            )}
            {isClosed && (
              <Button
                size="sm"
                variant="outline"
                disabled={saving}
                onClick={() => setStatus("open", "Ticket rouvert")}
                className="border-copper/30 text-copper-glow"
              >
                <RotateCcw className="mr-1.5 h-4 w-4" />
                Rouvrir le ticket
              </Button>
            )}
          </div>
        </div>

        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-5 p-4 pb-8">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className={cn("border", TYPE_STYLES[type].badge)}>
                {TYPE_STYLES[type].label}
              </Badge>
              {project && (
                <Badge
                  variant="outline"
                  className={cn("border", accent?.bg, accent?.color, accent?.border)}
                >
                  {project.name}
                </Badge>
              )}
              <Badge
                variant="outline"
                className={cn(
                  "border",
                  status === "done"
                    ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/25"
                    : status === "in_progress"
                      ? "bg-blue-500/15 text-blue-300 border-blue-500/25"
                      : "bg-copper/15 text-copper-glow border-copper/30"
                )}
              >
                {TICKET_STATUSES.find((s) => s.id === status)?.label ?? status}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-3 rounded-lg border border-copper/10 bg-obsidian/40 p-3 text-xs">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-titanium/50">
                  Priorité
                </p>
                <Select
                  value={priority}
                  onValueChange={(v) => handlePriorityChange(v as TicketPriority)}
                  disabled={saving}
                >
                  <SelectTrigger className="mt-1 h-8 border-copper/20 bg-obsidian text-xs">
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
              <div>
                <p className="text-[10px] uppercase tracking-wider text-titanium/50">
                  Statut avancé
                </p>
                <Select
                  value={status}
                  onValueChange={(v) => {
                    const msg =
                      v === "done"
                        ? "Ticket résolu"
                        : v === "wont_fix"
                          ? "Ticket classé won't fix"
                          : "Statut mis à jour";
                    setStatus(v as TicketStatus, msg);
                  }}
                  disabled={saving}
                >
                  <SelectTrigger className="mt-1 h-8 border-copper/20 bg-obsidian text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="border-copper/20 bg-surface-raised">
                    {TICKET_STATUSES.map(({ id, label }) => (
                      <SelectItem key={id} value={id}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-titanium/50">
                  Source
                </p>
                <p className="mt-1 text-ivory/80">
                  {SOURCE_LABELS[source] ?? ticket.source}
                </p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-titanium/50">
                  Créé le
                </p>
                <p className="mt-1 text-ivory/80">
                  {format(new Date(ticket.created_at), "d MMM yyyy", { locale: fr })}
                </p>
              </div>
            </div>

            {/* Description éditable */}
            <div>
              <div className="mb-2 flex items-center justify-between">
                <p className="text-[10px] uppercase tracking-wider text-titanium/50">
                  Description
                </p>
                {!editingDescription && (
                  <button
                    type="button"
                    onClick={() => setEditingDescription(true)}
                    className="flex items-center gap-1 text-[11px] text-copper-glow hover:underline"
                  >
                    <Pencil className="h-3 w-3" />
                    Modifier
                  </button>
                )}
              </div>

              {editingDescription ? (
                <div className="space-y-2">
                  <Textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={8}
                    disabled={saving}
                    placeholder="Décris le bug, les étapes pour reproduire, ce que tu as déjà tenté…"
                    className="border-copper/20 bg-obsidian text-ivory resize-none text-sm"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={saveDescription} disabled={saving}>
                      Enregistrer
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setDescription(ticket.description ?? "");
                        setEditingDescription(false);
                      }}
                    >
                      Annuler
                    </Button>
                  </div>
                </div>
              ) : (
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => setEditingDescription(true)}
                  onKeyDown={(e) => e.key === "Enter" && setEditingDescription(true)}
                  className="cursor-pointer rounded-lg border border-copper/10 bg-obsidian/60 p-3 transition hover:border-copper/20"
                >
                  {ticket.description ? (
                    <MarkdownContent className="prose prose-invert prose-sm max-w-none prose-p:text-titanium prose-li:text-titanium pointer-events-none">
                      {ticket.description}
                    </MarkdownContent>
                  ) : (
                    <p className="text-sm italic text-titanium/50">
                      Aucune description — clique pour en ajouter une
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Prompt Cursor — section secondaire */}
            <details className="rounded-lg border border-copper/10 bg-obsidian/30">
              <summary className="cursor-pointer px-3 py-2.5 text-sm text-titanium hover:text-ivory">
                <span className="inline-flex items-center gap-1.5">
                  <Zap className="h-3.5 w-3.5 text-emerald-400" />
                  Prompt Cursor (optionnel — pour implémenter dans l&apos;IDE)
                </span>
              </summary>
              <div className="space-y-2 border-t border-copper/10 p-3">
                {generating ? (
                  <div className="flex items-center gap-2 text-sm text-titanium">
                    <Loader2 className="h-4 w-4 animate-spin text-copper" />
                    Le Spec Agent analyse le ticket…
                  </div>
                ) : ticket.cursor_prompt ? (
                  <>
                    <pre className="max-h-48 overflow-auto rounded border border-copper/15 bg-obsidian p-3 text-[11px] text-ivory/85 whitespace-pre-wrap">
                      {ticket.cursor_prompt}
                    </pre>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={handleCopyPrompt}>
                        <Copy className="mr-1.5 h-3.5 w-3.5" />
                        Copier pour Cursor
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleGeneratePrompt}
                        className="text-emerald-400"
                      >
                        Regénérer
                      </Button>
                    </div>
                  </>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleGeneratePrompt}
                    className="w-full border-emerald-500/25 text-emerald-400"
                  >
                    <Zap className="mr-1.5 h-3.5 w-3.5" />
                    Générer un prompt Cursor
                  </Button>
                )}
              </div>
            </details>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCreateRoadmap}
              className="w-full border-copper/25 text-copper-glow hover:bg-copper/10"
            >
              <Map className="mr-2 h-4 w-4" />
              Ajouter à la roadmap
            </Button>
          </div>
        </ScrollArea>
      </aside>
    </>
  );
}
