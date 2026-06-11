"use client";

import { useState } from "react";
import { Loader2, RefreshCw, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
    <Card className="border-white/10 bg-surface/80">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-ivory">
          <Sparkles className="h-4 w-4 text-copper" />
          Résumé IA — agent comptabilité
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-titanium">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement du résumé…
          </div>
        ) : hasSummary ? (
          <MarkdownContent>{summary!.summary_md!}</MarkdownContent>
        ) : (
          <p className="text-sm text-titanium">
            Aucun résumé pour ce mois. Génère un aperçu avec l&apos;agent comptabilité.
          </p>
        )}

        <div className="flex justify-end">
          {hasSummary ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="border-white/10"
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
      </CardContent>
    </Card>
  );
}
