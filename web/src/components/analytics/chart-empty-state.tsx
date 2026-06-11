"use client";

import { BarChart3, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EMPTY_STATE_MESSAGE } from "@/components/analytics/analytics.constants";

interface ChartEmptyStateProps {
  onAddMetric?: () => void;
  compact?: boolean;
}

export function ChartEmptyState({ onAddMetric, compact }: ChartEmptyStateProps) {
  return (
    <div
      className={
        compact
          ? "flex min-h-[200px] flex-col items-center justify-center px-4 py-8 text-center"
          : "flex min-h-[280px] flex-col items-center justify-center px-6 py-12 text-center"
      }
    >
      <BarChart3 className="mb-3 h-8 w-8 text-titanium/40" />
      <p className="max-w-md text-sm leading-relaxed text-titanium">
        {EMPTY_STATE_MESSAGE}
      </p>
      {onAddMetric && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onAddMetric}
          className="mt-4 border-copper/30 text-copper-glow hover:bg-copper/10"
        >
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          Saisir une métrique
        </Button>
      )}
    </div>
  );
}
