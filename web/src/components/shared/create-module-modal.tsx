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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { createModule } from "@/lib/modules";
import type { ModuleStatus, ProjectModule } from "@/lib/types";

const STATUS_OPTIONS: { id: ModuleStatus; label: string }[] = [
  { id: "a_faire", label: "À faire" },
  { id: "en_developpement", label: "En développement" },
  { id: "en_test", label: "En test" },
  { id: "termine", label: "Terminé" },
];

interface CreateModuleModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  onCreated: (module: ProjectModule) => void;
}

export function CreateModuleModal({ open, onOpenChange, projectId, onCreated }: CreateModuleModalProps) {
  const [name, setName] = useState("");
  const [status, setStatus] = useState<ModuleStatus>("a_faire");
  const [featuresTotal, setFeaturesTotal] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setName("");
      setStatus("a_faire");
      setFeaturesTotal("");
    }
  }, [open]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Le nom du module est requis");
      return;
    }

    const total = Number(featuresTotal);
    setSubmitting(true);
    try {
      const created = await createModule({
        project_id: projectId,
        name: name.trim(),
        status,
        ...(featuresTotal.trim() && Number.isFinite(total) ? { features_total: total } : {}),
      });
      toast.success("Module créé");
      onCreated(created);
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
          <DialogTitle className="text-ivory">Nouveau module</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="module-name">Nom *</Label>
            <Input
              id="module-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={submitting}
              placeholder="Ex : Onboarding, Combat, Firmware…"
              className="border-copper/20 bg-obsidian text-ivory"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Statut initial</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as ModuleStatus)} disabled={submitting}>
                <SelectTrigger className="border-copper/20 bg-obsidian">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-copper/20 bg-surface-raised">
                  {STATUS_OPTIONS.map(({ id, label }) => (
                    <SelectItem key={id} value={id}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="module-features-total">Fonctionnalités prévues</Label>
              <Input
                id="module-features-total"
                type="number"
                min={0}
                value={featuresTotal}
                onChange={(e) => setFeaturesTotal(e.target.value)}
                disabled={submitting}
                placeholder="—"
                className="border-copper/20 bg-obsidian text-ivory"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
              className="border-copper/15"
            >
              Annuler
            </Button>
            <Button type="submit" disabled={submitting} className="bg-copper hover:bg-copper-glow">
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
