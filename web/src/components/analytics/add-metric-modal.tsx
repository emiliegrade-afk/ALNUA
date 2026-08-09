"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  METRIC_OPTIONS,
  METRIC_SOURCES,
} from "@/components/analytics/analytics.constants";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  createAnalyticsMetric,
  type AnalyticsMetricName,
} from "@/lib/analytics";
import { getProjectAccent } from "@/lib/projects";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AddMetricModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects: Project[];
  onCreated: () => void;
  defaultProjectId?: string;
}

export function AddMetricModal({
  open,
  onOpenChange,
  projects,
  onCreated,
  defaultProjectId,
}: AddMetricModalProps) {
  const [projectId, setProjectId] = useState(defaultProjectId ?? "");
  const [metricName, setMetricName] = useState<AnalyticsMetricName>("downloads");
  const [value, setValue] = useState("");
  const [metricDate, setMetricDate] = useState(
    () => new Date().toISOString().slice(0, 10)
  );
  const [source, setSource] = useState("stripe");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open && defaultProjectId) setProjectId(defaultProjectId);
    else if (open && projects.length && !projectId) {
      setProjectId(projects[0].id);
    }
  }, [open, defaultProjectId, projects, projectId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!projectId) {
      toast.error("Choisis un projet");
      return;
    }
    const num = parseFloat(value.replace(",", "."));
    if (Number.isNaN(num)) {
      toast.error("Valeur invalide");
      return;
    }

    setSubmitting(true);
    try {
      await createAnalyticsMetric({
        project_id: projectId,
        metric_name: metricName,
        value: num,
        metric_date: metricDate,
        source,
      });
      toast.success("Métrique enregistrée");
      onOpenChange(false);
      setValue("");
      onCreated();
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
          <DialogTitle className="text-ivory">Saisir une métrique</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Projet</Label>
            <Select value={projectId} onValueChange={setProjectId}>
              <SelectTrigger className="border-copper/20 bg-obsidian">
                <SelectValue placeholder="Projet" />
              </SelectTrigger>
              <SelectContent className="border-copper/20 bg-surface-raised">
                {projects.map((p) => {
                  const accent = getProjectAccent(p.branch);
                  return (
                    <SelectItem key={p.id} value={p.id}>
                      <span className="flex items-center gap-2">
                        <span
                          className={cn("h-1.5 w-1.5 rounded-full", accent.dot)}
                        />
                        {p.name}
                      </span>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Métrique</Label>
            <Select
              value={metricName}
              onValueChange={(v) => setMetricName(v as AnalyticsMetricName)}
            >
              <SelectTrigger className="border-copper/20 bg-obsidian">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-copper/20 bg-surface-raised">
                {METRIC_OPTIONS.map((m) => (
                  <SelectItem key={m.id} value={m.id}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Valeur</Label>
              <Input
                type="text"
                inputMode="decimal"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="0"
                className="border-copper/20 bg-obsidian"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Date</Label>
              <Input
                type="date"
                value={metricDate}
                onChange={(e) => setMetricDate(e.target.value)}
                className="border-copper/20 bg-obsidian"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Source</Label>
            <Select value={source} onValueChange={setSource}>
              <SelectTrigger className="border-copper/20 bg-obsidian">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-copper/20 bg-surface-raised">
                {METRIC_SOURCES.map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-copper/15"
            >
              Annuler
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="bg-copper hover:bg-copper-glow"
            >
              {submitting ? "Enregistrement…" : "Enregistrer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
