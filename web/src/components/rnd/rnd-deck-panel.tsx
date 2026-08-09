"use client";

import { useState } from "react";
import { ExternalLink, FileText, Info, Loader2, Presentation } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  dossierDeckFileUrl,
  generateDossierDeck,
} from "@/lib/rnd-dossier";

export interface RndDeckPanelProps {
  dossierId: string;
  dossierTitle: string;
  deckHtmlPath?: string | null;
  deckPdfPath?: string | null;
  onGenerated?: () => void;
}

export function RndDeckPanel({
  dossierId,
  dossierTitle,
  deckHtmlPath,
  deckPdfPath,
  onGenerated,
}: RndDeckPanelProps) {
  const [generating, setGenerating] = useState(false);
  const [lastSlideCount, setLastSlideCount] = useState<number | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const hasDeck = Boolean(deckHtmlPath);
  const hasPdf = Boolean(deckPdfPath);

  async function handleGenerate() {
    setGenerating(true);
    setPdfError(null);
    try {
      const result = await generateDossierDeck(dossierId);
      setLastSlideCount(result.slide_count);
      if (result.pdf_error) {
        setPdfError(result.pdf_error);
        toast.warning("Deck HTML prêt — PDF non exporté (voir détail ci-dessous)");
      } else {
        toast.success(result.message);
      }
      onGenerated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur génération deck");
    } finally {
      setGenerating(false);
    }
  }

  const htmlUrl = dossierDeckFileUrl(dossierId, "html");
  const pdfUrl = dossierDeckFileUrl(dossierId, "pdf");

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.06] p-4">
        <div className="mb-2 flex items-center gap-2 text-amber-200/90">
          <Info className="h-4 w-4 shrink-0" />
          <p className="text-sm font-medium">Ce n&apos;est pas le dossier CEO final</p>
        </div>
        <p className="text-xs leading-relaxed text-titanium/70">
          Le <strong className="font-normal text-ivory/85">deck pitch</strong> (phase 4) est une
          présentation slides pour partager l&apos;idée — extrait des sections R&D + finance.
          Le <strong className="font-normal text-ivory/85">dossier CEO</strong> (phase 6) regroupe
          executive summary, matrice dispatch et validation avant envoi au COO — voir l&apos;onglet{" "}
          <strong className="font-normal text-ivory/85">Dossier CEO</strong>.
        </p>
      </div>

      <div>
        <div className="mb-2 flex items-center gap-2">
          <Presentation className="h-5 w-5 text-copper" />
          <h2 className="font-title text-xl text-ivory">Deck pitch — intermédiaire</h2>
        </div>
        <p className="text-sm leading-relaxed text-titanium/70">
          Slides HTML/PDF à partir des sections du dossier{" "}
          <span className="text-ivory/90">{dossierTitle}</span>. Utile après comité ou avant
          revue CEO — pas le livrable de clôture.
        </p>
      </div>

      <div className="rounded-xl border border-copper/15 bg-obsidian-deep/40 p-5">
        <Button
          type="button"
          onClick={handleGenerate}
          disabled={generating}
          className="w-full bg-copper text-obsidian hover:bg-copper/90 sm:w-auto"
        >
          {generating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Génération…
            </>
          ) : (
            <>
              <Presentation className="mr-2 h-4 w-4" />
              {hasDeck ? "Regénérer le deck pitch" : "Générer le deck pitch"}
            </>
          )}
        </Button>

        {lastSlideCount != null ? (
          <p className="mt-3 text-xs text-titanium/55">
            {lastSlideCount} slide{lastSlideCount > 1 ? "s générées" : " générée"}
          </p>
        ) : null}

        {pdfError ? (
          <p className="mt-2 text-xs text-amber-200/80">
            PDF : {pdfError.slice(0, 200)}
            {pdfError.length > 200 ? "…" : ""}
          </p>
        ) : null}
      </div>

      {hasDeck ? (
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button
              type="button"
              variant="outline"
              className="border-copper/35 text-copper hover:bg-copper/10"
              asChild
            >
              <a href={htmlUrl} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                Ouvrir HTML (slides)
              </a>
            </Button>
            {hasPdf ? (
              <Button
                type="button"
                variant="outline"
                className="border-copper/15 text-ivory/90 hover:bg-obsidian-deep/50"
                asChild
              >
                <a href={pdfUrl} target="_blank" rel="noopener noreferrer" download>
                  <FileText className="mr-2 h-4 w-4" />
                  Télécharger PDF
                </a>
              </Button>
            ) : (
              <Button
                type="button"
                variant="outline"
                className="border-copper/15 text-titanium/80"
                asChild
              >
                <a href={htmlUrl} target="_blank" rel="noopener noreferrer">
                  <FileText className="mr-2 h-4 w-4" />
                  Imprimer en PDF (navigateur)
                </a>
              </Button>
            )}
          </div>
          {!hasPdf ? (
            <p className="text-xs text-titanium/50">
              PDF serveur absent — regénère le deck ou ouvre le HTML puis Ctrl+P → « Enregistrer
              en PDF ».
            </p>
          ) : null}
        </div>
      ) : (
        <p className="text-center text-xs text-titanium/45">
          Enrichissez le dossier (agents ou comité) avant la première génération.
        </p>
      )}
    </div>
  );
}
