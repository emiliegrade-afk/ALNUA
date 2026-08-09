"use client";

import { useState } from "react";
import { FolderPlus, Loader2 } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  submitRndProposal,
  type RndUserSubmitSections,
} from "@/lib/rnd";
import { cn } from "@/lib/utils";

const DOMAINS = [
  { id: "hub", label: "Hub ALNUA (infra interne)" },
  { id: "app", label: "App / SaaS produit" },
  { id: "gaming", label: "Jeu / Gaming" },
  { id: "hardware", label: "Hardware / IoT" },
  { id: "autre", label: "Autre" },
] as const;

const SECTION_FIELDS: {
  key: keyof RndUserSubmitSections;
  label: string;
  hint: string;
  rows: number;
  required?: boolean;
}[] = [
  {
    key: "problem",
    label: "Le problème",
    hint: "Quelle douleur résous-tu ? Pour qui ?",
    rows: 3,
    required: true,
  },
  {
    key: "solution",
    label: "La solution",
    hint: "Ta proposition de valeur en quelques phrases",
    rows: 3,
    required: true,
  },
  {
    key: "mvp",
    label: "MVP & périmètre v1",
    hint: "Ce que tu livres en premier — et ce que tu exclus",
    rows: 3,
  },
  {
    key: "market",
    label: "Marché & concurrence",
    hint: "Cible, concurrents nommés, différenciation",
    rows: 3,
  },
  {
    key: "feasibility",
    label: "Faisabilité",
    hint: "Stack, contraintes techniques, dépendances",
    rows: 2,
  },
  {
    key: "risks",
    label: "Risques",
    hint: "Ce qui pourrait bloquer — et comment tu mitiges",
    rows: 2,
  },
];

export interface RndSubmitDossierModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmitted?: (dossierId: string) => void;
}

export function RndSubmitDossierModal({
  open,
  onOpenChange,
  onSubmitted,
}: RndSubmitDossierModalProps) {
  const [title, setTitle] = useState("");
  const [tagline, setTagline] = useState("");
  const [domain, setDomain] = useState<string>("hub");
  const [whyNow, setWhyNow] = useState("");
  const [sections, setSections] = useState<RndUserSubmitSections>({});
  const [enrichWithAgents, setEnrichWithAgents] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  function resetForm() {
    setTitle("");
    setTagline("");
    setDomain("hub");
    setWhyNow("");
    setSections({});
    setEnrichWithAgents(false);
  }

  function setSection(key: keyof RndUserSubmitSections, value: string) {
    setSections((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      toast.error("Le titre est obligatoire");
      return;
    }
    if (!sections.problem?.trim() && !sections.solution?.trim()) {
      toast.error("Décris au minimum le problème ou la solution");
      return;
    }

    const cleanedSections: RndUserSubmitSections = {};
    for (const field of SECTION_FIELDS) {
      const val = sections[field.key]?.trim();
      if (val) cleanedSections[field.key] = val;
    }

    setSubmitting(true);
    try {
      const result = await submitRndProposal({
        title: title.trim(),
        tagline: tagline.trim() || undefined,
        domain,
        why_now: whyNow.trim() || undefined,
        sections: cleanedSections,
        enrich: enrichWithAgents,
      });
      toast.success(result.message);
      onOpenChange(false);
      resetForm();
      onSubmitted?.(result.dossier.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur de soumission");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        onOpenChange(next);
        if (!next) resetForm();
      }}
    >
      <DialogContent className="flex max-h-[90vh] flex-col border-copper/20 bg-surface-raised sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-ivory">
            <FolderPlus className="h-5 w-5 text-copper" />
            Soumettre un dossier R&D
          </DialogTitle>
          <DialogDescription className="text-titanium">
            Rédige ton pitch structuré — le pôle R&D (Alex, Idris, comité) reprendra
            à partir de tes sections.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="rnd-title" className="text-ivory/90">
                Titre du projet *
              </Label>
              <Input
                id="rnd-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ex: ALNUA Van Planner — offline first"
                className="border-copper/20 bg-obsidian text-ivory"
                maxLength={200}
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="rnd-tagline" className="text-ivory/90">
                Pitch en une phrase
              </Label>
              <Input
                id="rnd-tagline"
                value={tagline}
                onChange={(e) => setTagline(e.target.value)}
                placeholder="Le GPS des vanlifers qui marche sans réseau"
                className="border-copper/20 bg-obsidian text-ivory"
                maxLength={500}
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label className="text-ivory/90">Domaine</Label>
              <div className="flex flex-wrap gap-2">
                {DOMAINS.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => setDomain(d.id)}
                    className={cn(
                      "rounded-full border px-3 py-1 text-xs font-medium transition",
                      domain === d.id
                        ? "border-copper bg-copper/20 text-copper-glow"
                        : "border-copper/15 text-titanium hover:border-copper/30"
                    )}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-4 border-t border-copper/10 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-copper/80">
              Ton dossier
            </p>

            {SECTION_FIELDS.map((field) => (
              <div key={field.key} className="space-y-1.5">
                <Label htmlFor={`rnd-${field.key}`} className="text-ivory/85">
                  {field.label}
                  {field.required ? " *" : ""}
                </Label>
                <Textarea
                  id={`rnd-${field.key}`}
                  value={sections[field.key] ?? ""}
                  onChange={(e) => setSection(field.key, e.target.value)}
                  placeholder={field.hint}
                  rows={field.rows}
                  className="resize-none border-copper/15 bg-obsidian-deep/40 text-sm text-ivory/90"
                />
              </div>
            ))}

            <div className="space-y-1.5">
              <Label htmlFor="rnd-why-now" className="text-ivory/85">
                Pourquoi maintenant
              </Label>
              <Textarea
                id="rnd-why-now"
                value={whyNow}
                onChange={(e) => setWhyNow(e.target.value)}
                placeholder="Timing, tendance, fenêtre d'opportunité…"
                rows={2}
                className="resize-none border-copper/15 bg-obsidian-deep/40 text-sm text-ivory/90"
              />
            </div>
          </div>

          <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-copper/10 bg-obsidian-deep/40 p-3">
            <input
              type="checkbox"
              checked={enrichWithAgents}
              onChange={(e) => setEnrichWithAgents(e.target.checked)}
              className="mt-0.5 accent-copper"
            />
            <span className="text-xs leading-relaxed text-titanium/80">
              Enrichir avec les agents R&D après soumission (sections vides + business
              case). Tes textes ne seront pas écrasés.
            </span>
          </label>
        </form>

        <DialogFooter className="border-t border-copper/10 pt-4">
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
            className="bg-copper text-obsidian hover:bg-copper/90"
            onClick={handleSubmit}
          >
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Soumission…
              </>
            ) : (
              <>
                <FolderPlus className="mr-2 h-4 w-4" />
                Soumettre au pôle R&D
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
