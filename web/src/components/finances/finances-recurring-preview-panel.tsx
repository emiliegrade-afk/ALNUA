"use client";

import { CATEGORY_LABELS } from "@/components/finances/finances.constants";
import { formatCurrency } from "@/lib/finances-api";
import { getDedupedRecurringExpenses } from "@/lib/finances-recurring";
import type { FinanceTransaction } from "@/lib/finances-api";

export function FinancesRecurringPreviewPanel({
  recurringExpenses,
  onSeeAll,
}: {
  recurringExpenses: FinanceTransaction[];
  onSeeAll?: () => void;
}) {
  const deduped = getDedupedRecurringExpenses(recurringExpenses).sort(
    (a, b) => b.amount - a.amount,
  );
  const top = deduped.slice(0, 5);
  const total = deduped.reduce((sum, tx) => sum + tx.amount, 0);

  return (
    <div className="finance-instrument flex h-full flex-col p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[9px] font-medium uppercase tracking-[0.24em] text-titanium">
          SaaS
        </p>
        <span className="text-[10px] tabular-nums text-titanium/55">
          {deduped.length}
        </span>
      </div>
      {top.length === 0 ? (
        <p className="mt-4 text-xs text-titanium/50">Aucun récurrent.</p>
      ) : (
        <>
          <div className="mt-3 flex flex-col gap-2">
            {top.map((tx) => (
              <div key={tx.id} className="flex items-baseline justify-between gap-2">
                <span className="min-w-0 flex-1 truncate text-[12px] text-ivoire/90">
                  {tx.description?.trim() ||
                    CATEGORY_LABELS[tx.category] ||
                    tx.category}
                </span>
                <span className="shrink-0 text-[12px] tabular-nums text-titanium">
                  {formatCurrency(tx.amount, tx.currency)}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-auto flex items-center justify-between border-t border-titanium/10 pt-3">
            <span className="text-[10px] text-titanium/45">/ mois</span>
            <span className="text-[12px] tabular-nums text-ivoire">
              {formatCurrency(total)}
            </span>
          </div>
        </>
      )}
      {onSeeAll ? (
        <button
          type="button"
          onClick={onSeeAll}
          className="mt-3 w-full border border-titanium/15 py-1.5 text-center text-[10px] text-titanium transition-colors hover:border-copper/35 hover:text-copper-light"
        >
          Voir tout →
        </button>
      ) : null}
    </div>
  );
}
