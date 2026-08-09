import type { FinanceTransaction, Recurrence } from "./finances-api";

/* Dérivation pure sur les transactions récurrentes réelles — pas de nouvel
   endpoint, pas de donnée fabriquée. Partagé par le panneau "Prochaines
   échéances" et le panneau "Coûts récurrents" (redesign Vue Globale Finance).

   `dashboard.recurring_expenses` (backend) n'est pas filtré par type — peut
   contenir des revenus récurrents (ex. subvention) — on filtre ici sur
   `type === "expense"`. `is_recurring` peut aussi cohabiter avec plusieurs
   lignes historiques du même abonnement (aucun job ne génère une ligne par
   mois) — on déduplique par une clé de série approximative (project +
   catégorie + description), en gardant la transaction la plus récente. */

export interface UpcomingDue {
  key: string;
  label: string;
  amount: number;
  currency: string;
  lastDate: string;
  nextDue: string;
  overdue: boolean;
}

function seriesKey(tx: FinanceTransaction): string {
  return `${tx.project_id ?? ""}|${tx.category}|${(tx.description ?? "").trim().toLowerCase()}`;
}

/** Transactions dépense récurrentes réelles, dédupliquées (dernière
 * occurrence par série). Exclut `recurrence === "one_time"` — combinaison
 * `is_recurring=true` + `one_time` n'a pas de "prochaine occurrence" sensée. */
export function getDedupedRecurringExpenses(items: FinanceTransaction[]): FinanceTransaction[] {
  const byKey = new Map<string, FinanceTransaction>();
  for (const tx of items) {
    if (tx.type !== "expense" || !tx.is_recurring || tx.recurrence === "one_time" || !tx.recurrence) {
      continue;
    }
    const key = seriesKey(tx);
    const existing = byKey.get(key);
    if (!existing || tx.date > existing.date) byKey.set(key, tx);
  }
  return Array.from(byKey.values());
}

function addInterval(dateStr: string, recurrence: Exclude<Recurrence, "one_time">): string {
  const d = new Date(`${dateStr.slice(0, 10)}T00:00:00`);
  if (recurrence === "monthly") d.setMonth(d.getMonth() + 1);
  else d.setFullYear(d.getFullYear() + 1);
  return d.toISOString().slice(0, 10);
}

/** Estimation de la prochaine échéance — PAS une date fiscale officielle,
 * juste dernière occurrence + 1 période. Triée par échéance croissante. */
export function deriveUpcomingDue(items: FinanceTransaction[]): UpcomingDue[] {
  const today = new Date().toISOString().slice(0, 10);
  return getDedupedRecurringExpenses(items)
    .map((tx) => {
      const nextDue = addInterval(tx.date, tx.recurrence as Exclude<Recurrence, "one_time">);
      return {
        key: seriesKey(tx),
        label: tx.description?.trim() || tx.category,
        amount: tx.amount,
        currency: tx.currency,
        lastDate: tx.date,
        nextDue,
        overdue: nextDue < today,
      };
    })
    .sort((a, b) => a.nextDue.localeCompare(b.nextDue));
}
