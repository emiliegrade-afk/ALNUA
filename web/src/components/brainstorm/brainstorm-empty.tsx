"use client";

import { Lightbulb } from "lucide-react";
import { AlnuaLogo } from "@/components/brand/alnua-logo";
import { cn } from "@/lib/utils";

const DEFAULT_SUGGESTIONS = [
  "Nouvelles features pour le projet sélectionné",
  "Idée de nouveau produit ALNUA",
  "Comment améliorer la rétention utilisateurs ?",
  "Analyse concurrentielle rapide",
];

interface BrainstormEmptyProps {
  suggestions: string[];
  onSuggestionClick: (text: string) => void;
  layout?: "grid" | "inline";
}

export function BrainstormEmpty({
  suggestions,
  onSuggestionClick,
  layout = "grid",
}: BrainstormEmptyProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-6 text-center sm:px-6 sm:py-8">
      <AlnuaLogo variant="lockup" height={80} className="mb-6 sm:mb-8" />

      <p className="max-w-md text-sm leading-relaxed text-titanium sm:mt-2">
        Choisis un projet en haut, tape ton idée en bas, ou clique une suggestion.
      </p>

      <div
        className={cn(
          "mt-6 w-full max-w-lg gap-2 sm:mt-8 sm:gap-3",
          layout === "grid"
            ? "grid grid-cols-1 sm:grid-cols-2"
            : "flex flex-wrap justify-center"
        )}
      >
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSuggestionClick(s)}
            className="group flex items-start gap-2 rounded-xl border border-copper/20 bg-copper/[0.04] px-3 py-2.5 text-left text-sm text-titanium/80 transition hover:border-copper/40 hover:bg-copper/10 hover:text-copper-glow sm:px-4 sm:py-3"
          >
            <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-copper/70 group-hover:text-copper" />
            <span>{s}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export { DEFAULT_SUGGESTIONS };
