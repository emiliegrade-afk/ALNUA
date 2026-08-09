"use client";

import { CATEGORY_LABELS } from "@/components/finances/finances.constants";
import { formatCurrency } from "@/lib/finances-api";
import { deriveUpcomingDue } from "@/lib/finances-recurring";
import type { FinanceTransaction } from "@/lib/finances-api";
import { C } from "@/app/app-v2/shared";

/* "Prochaines échéances" — Vue Globale Finance (redesign). Estimation basée
   sur la dernière transaction récurrente réelle enregistrée, PAS une vraie
   échéance fiscale/bancaire officielle — le sous-texte le dit explicitement. */

export function FinancesUpcomingPanel({ recurringExpenses }: { recurringExpenses: FinanceTransaction[] }) {
  const upcoming = deriveUpcomingDue(recurringExpenses).slice(0, 5);

  return (
    <div className="rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
      <p className="text-[10.5px]" style={{ color: "#D8CFC4" }}>
        Prochaines échéances (estimation)
      </p>
      <p className="mt-0.5 text-[8.5px]" style={{ color: C.faint }}>
        Basé sur la dernière transaction récurrente enregistrée — pas une échéance officielle.
      </p>
      {upcoming.length === 0 ? (
        <p className="mt-3 text-[9.5px]" style={{ color: C.faint }}>
          Aucune dépense récurrente enregistrée.
        </p>
      ) : (
        <div className="mt-2.5 flex flex-col gap-2">
          {upcoming.map((u) => (
            <div key={u.key} className="flex items-center justify-between gap-2">
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[10.5px]" style={{ color: C.warm }}>
                  {CATEGORY_LABELS[u.label] ?? u.label}
                </span>
                <span className="block text-[8.5px]" style={{ color: u.overdue ? "#E0A95C" : C.faint }}>
                  {u.overdue ? "Estimée dépassée · " : ""}
                  {u.nextDue}
                </span>
              </span>
              <span className="shrink-0 text-[10.5px]" style={{ color: C.dim }}>
                {formatCurrency(u.amount)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
