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
import { upsertFunnelSnapshot, type FunnelSnapshot } from "@/lib/marketing-funnel-api";

/* Saisie mensuelle de l'entonnoir de conversion — Phase 37, ROADMAP.md.
   Volontairement manuel : ces chiffres viennent des analytics propres à
   chaque produit (App Store Connect, Play Console, Plausible/GA4, signups
   Supabase), pas d'un tracking centralisé qui n'existe pas côté Hub. */

const FIELDS = [
  { key: "visitors", label: "Visiteurs" },
  { key: "interested", label: "Intéressés" },
  { key: "engaged", label: "Engagés" },
  { key: "subscribers", label: "Abonnés" },
  { key: "customers", label: "Clients" },
] as const;

function currentMonthKey(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
}

interface FunnelEntryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  existing: FunnelSnapshot | null;
  onSaved: (snapshot: FunnelSnapshot) => void;
}

export function FunnelEntryModal({
  open,
  onOpenChange,
  projectId,
  existing,
  onSaved,
}: FunnelEntryModalProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [sourceNote, setSourceNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    if (existing) {
      setValues({
        visitors: String(existing.visitors),
        interested: String(existing.interested),
        engaged: String(existing.engaged),
        subscribers: String(existing.subscribers),
        customers: String(existing.customers),
      });
      setSourceNote(existing.source_note ?? "");
    } else {
      setValues({});
      setSourceNote("");
    }
  }, [open, existing]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!projectId) return;
    setSubmitting(true);
    try {
      const saved = await upsertFunnelSnapshot({
        project_id: projectId,
        period_month: existing?.period_month ?? currentMonthKey(),
        visitors: Math.max(0, parseInt(values.visitors, 10) || 0),
        interested: Math.max(0, parseInt(values.interested, 10) || 0),
        engaged: Math.max(0, parseInt(values.engaged, 10) || 0),
        subscribers: Math.max(0, parseInt(values.subscribers, 10) || 0),
        customers: Math.max(0, parseInt(values.customers, 10) || 0),
        source_note: sourceNote.trim() || null,
      });
      toast.success("Entonnoir mis à jour");
      onSaved(saved);
      onOpenChange(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-copper/15 bg-surface sm:max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-ivory">Chiffres du mois — entonnoir</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          {FIELDS.map((f) => (
            <div key={f.key} className="space-y-1.5">
              <Label htmlFor={`funnel-${f.key}`} className="text-xs">{f.label}</Label>
              <Input
                id={`funnel-${f.key}`}
                type="text"
                inputMode="numeric"
                value={values[f.key] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                placeholder="0"
                className="border-copper/15 bg-obsidian-deep/50"
              />
            </div>
          ))}
          <div className="space-y-1.5">
            <Label htmlFor="funnel-source" className="text-xs">Source (optionnel)</Label>
            <Input
              id="funnel-source"
              value={sourceNote}
              onChange={(e) => setSourceNote(e.target.value)}
              placeholder="Ex. Plausible + signups Supabase"
              className="border-copper/15 bg-obsidian-deep/50"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Enregistrement…" : "Enregistrer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
