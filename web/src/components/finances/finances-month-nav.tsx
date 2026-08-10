"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { formatMonthTitle } from "@/components/finances/finances.constants";
import { shiftMonth } from "@/lib/finances-api";

interface FinancesMonthNavProps {
  month: string;
  onChange: (month: string) => void;
}

export function FinancesMonthNav({ month, onChange }: FinancesMonthNavProps) {
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        className="flex h-7 w-7 items-center justify-center text-titanium/60 transition-colors hover:text-copper-light"
        onClick={() => onChange(shiftMonth(month, -1))}
        aria-label="Mois précédent"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      <h2 className="min-w-[140px] text-center text-[12px] font-medium uppercase tracking-[0.2em] text-titanium">
        {formatMonthTitle(month)}
      </h2>
      <button
        type="button"
        className="flex h-7 w-7 items-center justify-center text-titanium/60 transition-colors hover:text-copper-light"
        onClick={() => onChange(shiftMonth(month, 1))}
        aria-label="Mois suivant"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
