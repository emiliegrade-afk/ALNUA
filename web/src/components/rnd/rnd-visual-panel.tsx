"use client";

import { useCallback, useEffect, useState } from "react";
import { ImageIcon, Loader2, RefreshCw, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  dossierAssetFileUrl,
  fetchDossierAssets,
  generateDossierAssets,
  type RndDossierAsset,
} from "@/lib/rnd-dossier";

const ASSET_LABELS: Record<string, string> = {
  hero: "Hero — couverture",
  social_teaser: "Teaser réseaux",
  mockup: "Mockup produit",
  diagram: "Schéma MVP",
  moodboard: "Moodboard",
  chart: "Graphique finance",
};

export interface RndVisualPanelProps {
  dossierId: string;
  dossierTitle: string;
  onGenerated?: () => void;
}

export function RndVisualPanel({
  dossierId,
  dossierTitle,
  onGenerated,
}: RndVisualPanelProps) {
  const [assets, setAssets] = useState<RndDossierAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setAssets(await fetchDossierAssets(dossierId));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Impossible de charger les visuels");
      setAssets([]);
    } finally {
      setLoading(false);
    }
  }, [dossierId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleGenerate(force = false) {
    setGenerating(true);
    try {
      const result = await generateDossierAssets(dossierId, { force });
      setAssets(result.assets);
      toast.success(result.message);
      onGenerated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur génération visuels");
    } finally {
      setGenerating(false);
    }
  }

  const hasAssets = assets.length > 0;

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-copper" />
          <h2 className="font-title text-xl text-ivory">Visuels dossier</h2>
        </div>
        <p className="text-sm leading-relaxed text-titanium/70">
          Illustrations générées pour{" "}
          <span className="text-ivory/90">{dossierTitle}</span> — hero, mockup,
          moodboard et graphiques finance (Pillow, palette ALNUA).
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          onClick={() => void handleGenerate(hasAssets)}
          disabled={generating}
          className="bg-copper text-obsidian hover:bg-copper/90"
        >
          {generating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Génération…
            </>
          ) : (
            <>
              <ImageIcon className="mr-2 h-4 w-4" />
              {hasAssets ? "Regénérer les visuels" : "Générer les visuels"}
            </>
          )}
        </Button>
        {hasAssets ? (
          <Button
            type="button"
            variant="outline"
            disabled={generating}
            onClick={() => void load()}
            className="border-copper/15 text-titanium/80"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Actualiser
          </Button>
        ) : null}
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
        </div>
      ) : !hasAssets ? (
        <div className="rounded-xl border border-dashed border-copper/20 bg-obsidian-deep/40 p-10 text-center">
          <ImageIcon className="mx-auto mb-3 h-10 w-10 text-copper/25" />
          <p className="text-sm text-titanium/60">
            Aucun visuel pour l&apos;instant. Lance la génération après enrichissement
            du dossier (sections + finance pour le graphique).
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {assets.map((asset) => {
            const label =
              asset.metadata?.label ??
              ASSET_LABELS[asset.asset_type] ??
              asset.asset_type;
            const src = dossierAssetFileUrl(dossierId, asset.asset_type);
            return (
              <article
                key={asset.id}
                className="overflow-hidden rounded-xl border border-copper/15 bg-obsidian-deep/40"
              >
                <div className="border-b border-copper/10 px-3 py-2">
                  <p className="text-xs font-medium text-ivory/90">{label}</p>
                  <p className="text-[10px] text-titanium/50">
                    {asset.width}×{asset.height} · {asset.generation_model ?? "pillow"}
                  </p>
                </div>
                <div className="relative aspect-video bg-obsidian/60">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={src}
                    alt={label}
                    className="h-full w-full object-contain"
                    loading="lazy"
                  />
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
