"use client";

import { Download } from "lucide-react";
import { BrandAssetImage } from "@/components/brand/brand-asset-image";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { downloadAsset } from "@/lib/brand-api";
import { toast } from "sonner";

interface AssetGridProps {
  assets: Record<string, string>;
}

const ASSET_LABELS: Record<string, string> = {
  symbol_transparent: "Symbol",
  wordmark_transparent: "Wordmark",
  logo_dark_bg: "Logo dark",
  logo_light_bg: "Logo light",
};

function displayLabel(assetName: string): string {
  return ASSET_LABELS[assetName] ?? assetName.replace(/_/g, " ");
}

export function AssetGrid({ assets }: AssetGridProps) {
  const entries = Object.entries(assets);

  if (entries.length === 0) {
    return (
      <p className="text-sm text-titanium/70">
        Aucun asset isolé généré pour cette analyse.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {entries.map(([assetName, filePath]) => (
        <article
          key={assetName}
          className="overflow-hidden rounded-xl border border-copper/10 bg-obsidian/60 ring-1 ring-white/[0.04]"
        >
          <div
            className="relative flex aspect-square items-center justify-center p-4"
            style={{
              backgroundImage:
                "linear-gradient(45deg, #2a2a2a 25%, transparent 25%), linear-gradient(-45deg, #2a2a2a 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #2a2a2a 75%), linear-gradient(-45deg, transparent 75%, #2a2a2a 75%)",
              backgroundSize: "16px 16px",
              backgroundPosition: "0 0, 0 8px, 8px -8px, -8px 0",
              backgroundColor: "#14171C",
            }}
          >
            <BrandAssetImage
              filePath={filePath}
              alt={displayLabel(assetName)}
              className="max-h-full max-w-full object-contain"
            />
          </div>

          <div className="flex items-center justify-between gap-2 border-t border-copper/10 px-3 py-2">
            <Badge
              variant="outline"
              className="border-copper/30 bg-copper/10 text-copper"
            >
              {displayLabel(assetName)}
            </Badge>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 text-titanium hover:text-ivory"
              onClick={() => {
                void downloadAsset(assetName, filePath).catch(() => {
                  toast.error("Téléchargement impossible");
                });
              }}
            >
              <Download className="mr-1.5 h-3.5 w-3.5" />
              Télécharger
            </Button>
          </div>
        </article>
      ))}
    </div>
  );
}
