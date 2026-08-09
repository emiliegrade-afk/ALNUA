"use client";

import { useState } from "react";
import { Check, Loader2, RefreshCw, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  estimateDossierFinance,
  regenerateDossierSection,
  requestSectionRevision,
  validateDossierSection,
  type RndDossierSection,
} from "@/lib/rnd-dossier";

interface RndSectionActionsProps {
  dossierId: string;
  section: RndDossierSection;
  onUpdated: () => void;
}

export function RndSectionActions({
  dossierId,
  section,
  onUpdated,
}: RndSectionActionsProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const [revisionNote, setRevisionNote] = useState(section.revision_note ?? "");
  const [showRevision, setShowRevision] = useState(false);

  async function run(action: string, fn: () => Promise<unknown>) {
    setLoading(action);
    try {
      await fn();
      toast.success("Section mise à jour");
      onUpdated();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setLoading(null);
    }
  }

  const isFinance = section.section_key === "business_case";

  return (
    <div className="mt-4 space-y-3 border-t border-copper/10 pt-4">
      <div className="flex flex-wrap gap-2">
        {section.status !== "validated" ? (
          <Button
            size="sm"
            className="bg-emerald-600/90 hover:bg-emerald-600"
            disabled={!!loading}
            onClick={() =>
              run("validate", () =>
                validateDossierSection(dossierId, section.section_key)
              )
            }
          >
            {loading === "validate" ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Check className="mr-1 h-3.5 w-3.5" />
            )}
            Valider
          </Button>
        ) : null}

        <Button
          size="sm"
          variant="outline"
          className="border-copper/15"
          disabled={!!loading}
          onClick={() => setShowRevision((v) => !v)}
        >
          <RotateCcw className="mr-1 h-3.5 w-3.5" />
          Réviser
        </Button>

        <Button
          size="sm"
          variant="outline"
          className="border-copper/25 text-copper"
          disabled={!!loading}
          onClick={() =>
            run("regen", () =>
              isFinance
                ? estimateDossierFinance(dossierId, {
                    constraint: revisionNote || "recalculer",
                  })
                : regenerateDossierSection(dossierId, section.section_key, {
                    revision_note: revisionNote || "Améliorer et préciser",
                  })
            )
          }
        >
          {loading === "regen" ? (
            <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="mr-1 h-3.5 w-3.5" />
          )}
          {isFinance ? "Recalculer coûts" : "Régénérer"}
        </Button>
      </div>

      {showRevision ? (
        <div className="space-y-2">
          <Textarea
            value={revisionNote}
            onChange={(e) => setRevisionNote(e.target.value)}
            placeholder={
              isFinance
                ? "Ex: réduire les coûts de 30%, couper le scope marketing…"
                : "Note pour les agents : précisions, coupes scope, objections…"
            }
            rows={2}
            className="min-h-[60px] resize-none border-copper/15 bg-obsidian-deep/40 text-sm"
          />
          <Button
            size="sm"
            variant="outline"
            disabled={!!loading || !revisionNote.trim()}
            onClick={() =>
              run("request", () =>
                requestSectionRevision(dossierId, section.section_key, revisionNote.trim())
              )
            }
          >
            Demander révision (sans régénérer)
          </Button>
        </div>
      ) : null}
    </div>
  );
}
