"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus } from "lucide-react";
import { FinancesTransactionList } from "@/components/finances/finances-transaction-list";
import { FinancesRecurringSection } from "@/components/finances/finances-recurring-section";
import { fetchFinanceTransactions, type FinanceTransaction, type TransactionType } from "@/lib/finances-api";
import { C } from "../app-v2/shared";

/* Onglet "Transactions" — liste/CRUD embarqués tels quels (composants
   finances/ existants, logique non triviale, pas de reskin). Phase 29,
   ROADMAP.md. */

export function TransactionsTab({
  month,
  refreshKey,
  onAdd,
  onEdit,
}: {
  month: string;
  refreshKey: number;
  onAdd: () => void;
  onEdit: (tx: FinanceTransaction) => void;
}) {
  const [transactions, setTransactions] = useState<FinanceTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<"all" | TransactionType>("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [localTick, setLocalTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchFinanceTransactions({
      month,
      type: typeFilter === "all" ? undefined : typeFilter,
      category: categoryFilter === "all" ? undefined : categoryFilter,
    })
      .then((txs) => {
        if (!cancelled) setTransactions(txs);
      })
      .catch(() => {
        if (!cancelled) setTransactions([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [month, typeFilter, categoryFilter, refreshKey, localTick]);

  const recurring = useMemo(() => transactions.filter((t) => t.is_recurring), [transactions]);

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-1">
      <div className="flex justify-end">
        <button
          type="button"
          onClick={onAdd}
          className="flex items-center gap-1.5 rounded-[18px] border px-[13px] py-1.5 text-[11.5px]"
          style={{ borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.08)", color: C.copperLight }}
        >
          <Plus className="h-3.5 w-3.5" /> Ajouter une transaction
        </button>
      </div>

      {loading && transactions.length === 0 ? (
        <p className="text-center text-[11px]" style={{ color: C.faint }}>
          Chargement des transactions…
        </p>
      ) : (
        <FinancesTransactionList
          transactions={transactions}
          typeFilter={typeFilter}
          categoryFilter={categoryFilter}
          onTypeFilterChange={setTypeFilter}
          onCategoryFilterChange={setCategoryFilter}
          onEdit={onEdit}
          onDeleted={() => setLocalTick((t) => t + 1)}
        />
      )}

      <FinancesRecurringSection items={recurring} onManage={onEdit} />
    </div>
  );
}
