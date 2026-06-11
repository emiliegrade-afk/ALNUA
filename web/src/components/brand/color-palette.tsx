"use client";

import { toast } from "sonner";
import type { ColorInfo } from "@/lib/brand-api";

interface ColorPaletteProps {
  colors: ColorInfo[];
}

function sourceLabel(source: ColorInfo["source"] | undefined): string {
  if (source === "kmeans") return "K-means";
  if (source === "llm") return "LLM";
  if (source === "merged") return "Merged";
  return "LLM";
}

export function ColorPalette({ colors }: ColorPaletteProps) {
  async function copyHex(hex: string) {
    try {
      await navigator.clipboard.writeText(hex);
      toast.success("Copié !");
    } catch {
      toast.error("Impossible de copier la couleur.");
    }
  }

  if (colors.length === 0) {
    return (
      <p className="text-sm text-titanium/70">Aucune couleur détectée.</p>
    );
  }

  return (
    <div className="flex flex-wrap gap-4">
      {colors.map((color, index) => (
        <div key={`${color.hex}-${index}`} className="flex flex-col items-center gap-1">
          <button
            type="button"
            title={`${color.hex} — ${color.name}`}
            onClick={() => copyHex(color.hex)}
            className="h-10 w-10 rounded-lg border border-white/10 shadow-sm transition-transform hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/60"
            style={{ backgroundColor: color.hex }}
            aria-label={`Copier ${color.hex}, ${color.name}`}
          />
          <span className="text-[10px] uppercase tracking-wider text-titanium/60">
            {sourceLabel(color.source)}
          </span>
        </div>
      ))}
    </div>
  );
}
