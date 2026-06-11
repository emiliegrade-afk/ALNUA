"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ProjectSelector } from "@/components/shared/project-selector";
import { fetchProjects } from "@/lib/api";
import {
  getStoredProjectId,
  getTodayCaptureCount,
  incrementTodayCaptureCount,
  quickCapture,
  storeProjectId,
  type QuickCapturePriority,
  type QuickCaptureType,
} from "@/lib/quick-capture";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

const CAPTURE_TYPES: {
  id: QuickCaptureType;
  emoji: string;
  label: string;
}[] = [
  { id: "ticket", emoji: "🐛", label: "Bug/Ticket" },
  { id: "idea", emoji: "💡", label: "Idée" },
  { id: "roadmap", emoji: "🗺️", label: "Roadmap" },
  { id: "note", emoji: "📝", label: "Note libre" },
];

const PRIORITIES: { id: QuickCapturePriority; label: string }[] = [
  { id: "critical", label: "Critical" },
  { id: "high", label: "High" },
  { id: "medium", label: "Medium" },
  { id: "low", label: "Low" },
];

const TYPE_LABELS: Record<QuickCaptureType, string> = {
  ticket: "Bug/Ticket",
  idea: "Idée",
  roadmap: "Roadmap",
  note: "Note",
};

export function QuickCaptureButton() {
  const router = useRouter();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [open, setOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [content, setContent] = useState("");
  const [captureType, setCaptureType] = useState<QuickCaptureType>("note");
  const [projectId, setProjectId] = useState("");
  const [priority, setPriority] = useState<QuickCapturePriority>("medium");
  const [submitting, setSubmitting] = useState(false);
  const [todayCount, setTodayCount] = useState(0);

  const showPriority = captureType === "ticket" || captureType === "roadmap";

  const resetForm = useCallback(() => {
    setContent("");
    setCaptureType("note");
    setPriority("medium");
    const stored = getStoredProjectId();
    if (stored && projects.some((p) => p.id === stored)) {
      setProjectId(stored);
    } else if (projects[0]) {
      setProjectId(projects[0].id);
    }
  }, [projects]);

  useEffect(() => {
    setTodayCount(getTodayCaptureCount());
    fetchProjects()
      .then((list) => {
        setProjects(list);
        const stored = getStoredProjectId();
        if (stored && list.some((p) => p.id === stored)) {
          setProjectId(stored);
        } else if (list[0]) {
          setProjectId(list[0].id);
        }
      })
      .catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    if (open) {
      resetForm();
      const timer = window.setTimeout(() => textareaRef.current?.focus(), 50);
      return () => window.clearTimeout(timer);
    }
  }, [open, resetForm]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.ctrlKey && e.shiftKey && e.code === "Space") {
        e.preventDefault();
        setOpen(true);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function handleProjectChange(value: string, id: string | null) {
    if (id) {
      setProjectId(id);
      storeProjectId(id);
    }
  }

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    if (!content.trim()) {
      toast.error("Décris ton idée, bug ou tâche");
      return;
    }
    if (!projectId) {
      toast.error("Sélectionne un projet");
      return;
    }

    setSubmitting(true);
    try {
      const result = await quickCapture({
        type: captureType,
        content: content.trim(),
        project_id: projectId,
        ...(showPriority ? { priority } : {}),
      });

      storeProjectId(projectId);
      const count = incrementTodayCaptureCount();
      setTodayCount(count);
      setOpen(false);

      toast(
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span>✓ {TYPE_LABELS[result.type]} capturé</span>
          <button
            type="button"
            className="font-medium text-copper hover:text-copper-glow hover:underline"
            onClick={() => router.push(result.redirect_url)}
          >
            Voir →
          </button>
        </div>,
        { duration: 4000 }
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur de capture");
    } finally {
      setSubmitting(false);
    }
  }

  function handleTextareaKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.ctrlKey && e.key === "Enter") {
      e.preventDefault();
      void handleSubmit();
    }
  }

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Capturer rapidement (Ctrl+Shift+Espace)"
          className={cn(
            "fixed bottom-6 right-6 z-[9999] flex h-14 w-14 items-center justify-center",
            "rounded-full bg-copper text-white shadow-lg shadow-black/30",
            "transition-transform duration-150 hover:scale-110",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper focus-visible:ring-offset-2 focus-visible:ring-offset-obsidian"
          )}
        >
          <Plus className="h-6 w-6" strokeWidth={2.5} />
          {todayCount > 0 && (
            <span
              className="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white ring-2 ring-obsidian"
              aria-label={`${todayCount} capture${todayCount > 1 ? "s" : ""} aujourd'hui`}
            >
              {todayCount > 9 ? "9+" : todayCount}
            </span>
          )}
        </button>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="border-copper/20 bg-surface-raised sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle className="text-ivory">Capturer rapidement</DialogTitle>
            <DialogDescription className="text-titanium">
              Vers quel endroit ?
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Textarea
                ref={textareaRef}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                onKeyDown={handleTextareaKeyDown}
                rows={3}
                placeholder="Décris l'idée, le bug, la tâche..."
                className="resize-none border-copper/20 bg-obsidian text-ivory placeholder:text-titanium/60"
              />
              <p className="text-xs text-titanium/70">Ctrl+Entrée pour soumettre</p>
            </div>

            <div className="space-y-2">
              <Label className="text-ivory/80">Type</Label>
              <div className="grid grid-cols-2 gap-2">
                {CAPTURE_TYPES.map((t) => {
                  const selected = captureType === t.id;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setCaptureType(t.id)}
                      className={cn(
                        "flex items-center gap-2 rounded-lg border px-3 py-2.5 text-left text-sm transition-colors",
                        selected
                          ? "border-copper bg-copper/15 text-ivory"
                          : "border-white/10 bg-white/[0.02] text-ivory/80 hover:border-copper/30 hover:bg-white/[0.04]"
                      )}
                    >
                      <span className="text-base" aria-hidden>
                        {t.emoji}
                      </span>
                      <span className="font-medium">{t.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-ivory/80">Projet</Label>
              <ProjectSelector
                projects={projects}
                value={projectId}
                onChange={handleProjectChange}
                onProjectsUpdated={setProjects}
                mode="picker"
                className="w-full"
                triggerClassName="w-full"
                contentClassName="z-[100]"
                placeholder="Choisir un projet"
              />
            </div>

            {showPriority && (
              <div className="space-y-2">
                <Label className="text-ivory/80">Priorité</Label>
                <div className="flex flex-wrap gap-2">
                  {PRIORITIES.map((p) => {
                    const selected = priority === p.id;
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => setPriority(p.id)}
                        className={cn(
                          "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                          selected
                            ? "border-copper bg-copper/20 text-copper-glow"
                            : "border-white/10 text-titanium hover:border-copper/30 hover:text-ivory"
                        )}
                      >
                        {p.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            <DialogFooter className="border-t-0 bg-transparent p-0 sm:justify-end">
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                className="border-white/10"
              >
                Annuler
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                className="bg-copper hover:bg-copper-glow"
              >
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Capturer →
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
