"use client";

import { Download } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BrandAssetImage } from "@/components/brand/brand-asset-image";
import {
  FORMAT_CATEGORIES,
  FORMAT_DIMENSIONS,
  FORMAT_LABELS,
  downloadAsset,
} from "@/lib/brand-api";

interface FormatGridProps {
  assets: Record<string, string>;
}

function displayLabel(formatName: string): string {
  return FORMAT_LABELS[formatName] ?? formatName.replace(/_/g, " ");
}

export function FormatGrid({ assets }: FormatGridProps) {
  const categories = Object.entries(FORMAT_CATEGORIES).filter(([, cat]) =>
    cat.formats.some((name) => name in assets)
  );

  if (categories.length === 0) {
    return (
      <p className="text-sm text-titanium/70">
        Aucun format généré pour ce kit.
      </p>
    );
  }

  return (
    <div className="space-y-8">
      {categories.map(([key, category]) => {
        const items = category.formats.filter((name) => name in assets);
        if (items.length === 0) return null;

        return (
          <section key={key}>
            <h3 className="mb-3 text-xs font-medium uppercase tracking-widest text-titanium">
              {category.label}
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {items.map((formatName) => {
                const filePath = assets[formatName];
                const isWide =
                  formatName.includes("banner") ||
                  formatName.includes("cover") ||
                  formatName.includes("header") ||
                  formatName === "wordmark_transparent" ||
                  formatName === "logo_horizontal";

                return (
                  <article
                    key={formatName}
                    className="overflow-hidden rounded-xl border border-copper/10 bg-obsidian/60 ring-1 ring-copper/10"
                  >
                    <div
                      className={`relative flex items-center justify-center p-3 ${
                        isWide ? "aspect-[21/9]" : "aspect-square"
                      }`}
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
                        alt={displayLabel(formatName)}
                        className="max-h-full max-w-full object-contain"
                      />
                    </div>

                    <div className="space-y-2 border-t border-copper/10 px-3 py-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge
                          variant="outline"
                          className="border-copper/30 bg-copper/10 text-copper"
                        >
                          {displayLabel(formatName)}
                        </Badge>
                        <span className="text-[10px] text-titanium/60">
                          {FORMAT_DIMENSIONS[formatName] ?? "—"}
                        </span>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-8 w-full text-titanium hover:text-ivory"
                        onClick={() => {
                          void downloadAsset(formatName, filePath).catch(() => undefined);
                        }}
                      >
                        <Download className="mr-1.5 h-3.5 w-3.5" />
                        Télécharger
                      </Button>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
