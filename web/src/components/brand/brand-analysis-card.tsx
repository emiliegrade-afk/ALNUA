"use client";

import { ColorPalette } from "@/components/brand/color-palette";
import { Badge } from "@/components/ui/badge";
import type { BrandAnalysis } from "@/lib/brand-api";

interface BrandAnalysisCardProps {
  analysis: BrandAnalysis;
}

export function BrandAnalysisCard({ analysis }: BrandAnalysisCardProps) {
  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-xl font-semibold text-ivory">{analysis.brand_name}</h3>
        {analysis.tagline && (
          <p className="mt-1 text-sm text-titanium">{analysis.tagline}</p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge
          variant="outline"
          className="border-copper/30 bg-copper/10 text-copper"
        >
          {analysis.style}
        </Badge>
        {analysis.mood.map((m) => (
          <Badge
            key={m}
            variant="secondary"
            className="bg-obsidian text-titanium"
          >
            {m}
          </Badge>
        ))}
      </div>

      <div>
        <h4 className="mb-2 text-xs font-medium uppercase tracking-widest text-titanium">
          Palette
        </h4>
        <ColorPalette colors={analysis.colors} />
      </div>

      {analysis.elements.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-medium uppercase tracking-widest text-titanium">
            Éléments détectés
          </h4>
          <ul className="space-y-2">
            {analysis.elements.map((element, index) => (
              <li
                key={`${element.label}-${index}`}
                className="flex items-center justify-between rounded-lg border border-copper/10 bg-obsidian-deep/50 px-3 py-2 text-sm"
              >
                <span className="font-medium text-ivory">{element.label}</span>
                <Badge variant="outline" className="text-titanium">
                  {element.type}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      )}

      {analysis.typography_style && (
        <p className="text-xs text-titanium/80">
          Typo : {analysis.typography_style}
        </p>
      )}

      {analysis.usage_notes && (
        <p className="text-sm leading-relaxed text-titanium/90">
          {analysis.usage_notes}
        </p>
      )}
    </div>
  );
}
