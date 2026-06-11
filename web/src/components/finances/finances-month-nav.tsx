"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatMonthTitle } from "@/components/finances/finances.constants";
import { shiftMonth } from "@/lib/finances-api";

interface FinancesMonthNavProps {
  month: string;
  onChange: (month: string) => void;
}

export function FinancesMonthNav({ month, onChange }: FinancesMonthNavProps) {
  return (
    <div className="flex items-center justify-center gap-3">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-9 w-9 text-titanium hover:text-ivory"
        onClick={() => onChange(shiftMonth(month, -1))}
        aria-label="Mois précédent"
      >
        <ChevronLeft className="h-5 w-5" />
      </Button>
      <h2 className="min-w-[160px] text-center text-lg font-medium capitalize text-ivory">
        {formatMonthTitle(month)}
      </h2>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-9 w-9 text-titanium hover:text-ivory"
        onClick={() => onChange(shiftMonth(month, 1))}
        aria-label="Mois suivant"
      >
        <ChevronRight className="h-5 w-5" />
      </Button>
    </div>
  );
}
