"use client";

import { CATEGORY_LABELS } from "@/components/finances/finances.constants";
import { formatCurrency } from "@/lib/finances-api";
import { getDedupedRecurringExpenses } from "@/lib/finances-recurring";
import type { FinanceTransaction } from "@/lib/finances-api";
import { C } from "@/app/app-v2/shared";

/* "Coûts récurrents" — Vue Globale Finance (redesign). PAS "Abonnements SaaS
   actifs" : les transactions n'ont pas de champ date-de-renouvellement, donc
   pas de promesse de suivi d'abonnement — juste les dépenses réelles
   marquées récurrentes, dédupliquées par série. Liste complète et non
   dédupliquée disponible dans l'onglet Transactions (FinancesRecurringSection). */

export function FinancesRecurringPreviewPanel({
  recurringExpenses,
  onSeeAll,
}: {
  recurringExpenses: FinanceTransaction[];
  onSeeAll?: () => void;
}) {
  const deduped = getDedupedRecurringExpenses(recurringExpenses).sort((a, b) => b.amount - a.amount);
  const top = deduped.slice(0, 5);
  const total = deduped.reduce((sum, tx) => sum + tx.amount, 0);

  return (
    <div className="rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
      <div className="flex items-center justify-between">
        <p className="text-[10.5px]" style={{ color: "#D8CFC4" }}>
          Coûts récurrents
        </p>
        <span className="rounded-full px-1.5 py-0.5 text-[9px]" style={{ background: "rgba(192,138,114,.12)", color: C.copperLight }}>
          {deduped.length}
        </span>
      </div>
      {top.length === 0 ? (
        <p className="mt-3 text-[9.5px]" style={{ color: C.faint }}>
          Aucun coût récurrent enregistré.
        </p>
      ) : (
        <>
          <div className="mt-2.5 flex flex-col gap-2">
            {top.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between gap-2">
                <span className="min-w-0 flex-1 truncate text-[10.5px]" style={{ color: C.warm }}>
                  {tx.description?.trim() || CATEGORY_LABELS[tx.category] || tx.category}
                </span>
                <span className="shrink-0 text-[10.5px]" style={{ color: C.dim }}>
                  {formatCurrency(tx.amount, tx.currency)}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-2.5 flex items-center justify-between border-t pt-2" style={{ borderColor: C.lineSoft }}>
            <span className="text-[9px]" style={{ color: C.faint }}>
              Total estimé / mois
            </span>
            <span className="text-[10.5px] font-semibold" style={{ color: C.ivory }}>
              {formatCurrency(total)}
            </span>
          </div>
        </>
      )}
      {onSeeAll ? (
        <button
          type="button"
          onClick={onSeeAll}
          className="mt-2.5 w-full rounded-lg border py-1.5 text-center text-[9.5px]"
          style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}
        >
          Voir tout dans Transactions →
        </button>
      ) : null}
    </div>
  );
}
