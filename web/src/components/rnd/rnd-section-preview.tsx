"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Circle, Loader2, Pencil } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { RndSectionActions } from "@/components/rnd/rnd-section-actions";
import { updateDossierSection, type RndDossierSection } from "@/lib/rnd-dossier";

/* Extrait de rnd-dossier-workspace.tsx (correctif Phase 27, ROADMAP.md) —
   étaient des fonctions privées (non exportées), donc inutilisables ailleurs.
   Comportement inchangé, réutilisé tel quel par rnd-dossier-workspace.tsx (/rd)
   et rnd-dossier-sections-panel.tsx (rnd-v2). */

export function SectionStatusIcon({ status }: { status: string }) {
  if (status === "validated") {
    return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
  }
  if (status === "needs_revision") {
    return <Circle className="h-3.5 w-3.5 text-amber-400" />;
  }
  if (status === "under_review") {
    return <Circle className="h-3.5 w-3.5 text-copper/70" />;
  }
  return <Circle className="h-3.5 w-3.5 text-titanium/40" />;
}

export function SectionPreview({
  section,
  dossierId,
  onUpdated,
}: {
  section: RndDossierSection;
  dossierId: string;
  onUpdated: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(section.content_md);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!editing) setDraft(section.content_md);
  }, [section.content_md, editing]);

  async function saveEdit() {
    if (!draft.trim()) {
      toast.error("Le contenu ne peut pas être vide");
      return;
    }
    setSaving(true);
    try {
      await updateDossierSection(dossierId, section.section_key, draft.trim());
      toast.success("Section enregistrée");
      setEditing(false);
      onUpdated();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-xl border border-copper/10 bg-obsidian-deep/40 p-4">
      <div className="mb-2 flex items-center gap-2">
        <SectionStatusIcon status={section.status} />
        <h3 className="text-sm font-semibold text-ivory/90">{section.title}</h3>
        <span className="ml-auto text-[10px] text-titanium/50">{section.status}</span>
        {!editing && section.section_key !== "business_case" ? (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-titanium/60 hover:text-ivory"
            onClick={() => setEditing(true)}
          >
            <Pencil className="mr-1 h-3 w-3" />
            Éditer
          </Button>
        ) : null}
      </div>
      {editing ? (
        <div className="space-y-2">
          <Textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={8}
            className="resize-y border-copper/15 bg-obsidian-deep/40 font-mono text-sm text-ivory/90"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              className="bg-copper text-obsidian hover:bg-copper/90"
              disabled={saving}
              onClick={() => void saveEdit()}
            >
              {saving ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : null}
              Enregistrer
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="border-copper/15"
              disabled={saving}
              onClick={() => {
                setDraft(section.content_md);
                setEditing(false);
              }}
            >
              Annuler
            </Button>
          </div>
        </div>
      ) : (
        <div className="prose prose-invert max-w-none text-sm leading-relaxed text-titanium/80">
          <pre className="whitespace-pre-wrap font-sans text-sm">{section.content_md}</pre>
        </div>
      )}
      <RndSectionActions dossierId={dossierId} section={section} onUpdated={onUpdated} />
    </section>
  );
}
