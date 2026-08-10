"use client";

import { CATEGORY_LABELS } from "@/components/finances/finances.constants";
import { formatCurrency } from "@/lib/finances-api";
import { deriveUpcomingDue } from "@/lib/finances-recurring";
import type { FinanceTransaction } from "@/lib/finances-api";

/* "Prochaines échéances" — estimation depuis récurrents réels. */

export function FinancesUpcomingPanel({
  recurringExpenses,
}: {
  recurringExpenses: FinanceTransaction[];
}) {
  const upcoming = deriveUpcomingDue(recurringExpenses).slice(0, 5);

  return (
    <div className="finance-instrument flex h-full flex-col p-4">
      <p className="text-[9px] font-medium uppercase tracking-[0.24em] text-titanium">
        Échéances
      </p>
      {upcoming.length === 0 ? (
        <p className="mt-4 text-xs text-titanium/50">Aucun récurrent.</p>
      ) : (
        <div className="mt-3 flex flex-col gap-2.5">
          {upcoming.map((u) => (
            <div key={u.key} className="flex items-baseline justify-between gap-2">
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[12px] text-ivoire/90">
                  {CATEGORY_LABELS[u.label] ?? u.label}
                </span>
                <span
                  className={`block text-[10px] ${u.overdue ? "text-amber-400/80" : "text-titanium/50"}`}
                >
                  {u.nextDue}
                </span>
              </span>
              <span className="shrink-0 text-[12px] tabular-nums text-titanium">
                {formatCurrency(u.amount)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
