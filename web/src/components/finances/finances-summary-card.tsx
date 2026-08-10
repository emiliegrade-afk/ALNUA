"use client";

import { useState } from "react";
import { Loader2, RefreshCw, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { Button } from "@/components/ui/button";
import {
  fetchFinanceSummary,
  regenerateFinanceSummary,
  type FinancialSummary,
} from "@/lib/finances-api";

interface FinancesSummaryCardProps {
  month: string;
  summary: FinancialSummary | null;
  loading: boolean;
  onUpdated: (summary: FinancialSummary) => void;
}

export function FinancesSummaryCard({
  month,
  summary,
  loading,
  onUpdated,
}: FinancesSummaryCardProps) {
  const [generating, setGenerating] = useState(false);

  async function handleGenerate(force = false) {
    setGenerating(true);
    try {
      const result = force
        ? await regenerateFinanceSummary(month)
        : await fetchFinanceSummary(month);
      onUpdated(result);
      toast.success(force ? "Résumé régénéré" : "Résumé généré");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur de génération");
    } finally {
      setGenerating(false);
    }
  }

  const hasSummary = Boolean(summary?.summary_md?.trim());

  return (
    <div className="finance-instrument flex h-full flex-col p-4">
      <div className="mb-3 flex items-center gap-2">
        <Sparkles className="h-3 w-3 text-copper/80" aria-hidden />
        <h3 className="text-[9px] font-medium uppercase tracking-[0.24em] text-titanium">
          Résumé IA
        </h3>
      </div>
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-titanium/70">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement du résumé…
          </div>
        ) : hasSummary ? (
          <MarkdownContent>{summary!.summary_md!}</MarkdownContent>
        ) : (
          <p className="text-sm text-titanium/60">
            Aucun résumé pour ce mois. Génère un aperçu avec l&apos;agent
            comptabilité.
          </p>
        )}

        <div className="flex justify-end">
          {hasSummary ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="border-copper/30 text-copper-light hover:border-copper/50 hover:bg-copper/10"
              disabled={generating}
              onClick={() => handleGenerate(true)}
            >
              {generating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Regénérer le résumé
            </Button>
          ) : (
            <Button
              type="button"
              size="sm"
              className="bg-copper/90 text-void hover:bg-copper"
              disabled={generating}
              onClick={() => handleGenerate(false)}
            >
              {generating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
              )}
              Générer le résumé du mois
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
