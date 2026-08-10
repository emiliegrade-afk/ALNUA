"use client";

import { useEffect, useMemo, useState } from "react";
import {
  fetchFinanceTransactions,
  formatCurrency,
  type FinanceTransaction,
} from "@/lib/finances-api";
import type { Project } from "@/lib/types";
import { Bar } from "@/app/app-v2/shared";

/* "Dépenses par branche produit" — projects.branch (app/gaming/robotics/other).
   Bucket "Sans projet" toujours visible. */

const BRANCH_LABELS: Record<string, string> = {
  app: "App",
  gaming: "Gaming",
  robotics: "Robotique",
  other: "Autre",
  none: "Sans projet (dépense générale)",
};

export function FinancesBranchBreakdownPanel({
  month,
  projects,
}: {
  month: string;
  projects: Project[];
}) {
  const [transactions, setTransactions] = useState<FinanceTransaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchFinanceTransactions({ month, type: "expense" })
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
  }, [month]);

  const byBranch = useMemo(() => {
    const projectById = new Map(projects.map((p) => [p.id, p]));
    const totals: Record<string, number> = {};
    for (const tx of transactions) {
      const branch = tx.project_id
        ? (projectById.get(tx.project_id)?.branch ?? "other")
        : "none";
      totals[branch] = (totals[branch] ?? 0) + tx.amount;
    }
    const max = Math.max(1, ...Object.values(totals));
    return Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .map(([branch, amount]) => ({
        branch,
        amount,
        pct: Math.round((amount / max) * 100),
      }));
  }, [transactions, projects]);

  return (
    <div className="finance-instrument flex h-full flex-col p-4">
      <p className="text-[9px] font-medium uppercase tracking-[0.24em] text-titanium">
        Par branche
      </p>
      <p className="mt-1 text-[10px] text-titanium/50">
        Basé sur les transactions liées à un projet.
      </p>
      {loading && transactions.length === 0 ? (
        <p className="mt-4 text-sm text-titanium/55">Chargement…</p>
      ) : byBranch.length === 0 ? (
        <p className="mt-4 text-sm text-titanium/55">
          Aucune dépense ce mois-ci.
        </p>
      ) : (
        <div className="mt-4 flex flex-col gap-3">
          {byBranch.map(({ branch, amount, pct }) => (
            <div key={branch} className="flex items-center gap-2">
              <span className="w-[140px] shrink-0 truncate text-xs text-ivoire">
                {BRANCH_LABELS[branch] ?? branch}
              </span>
              <Bar value={pct} thick={4} />
              <span className="w-[72px] shrink-0 text-right text-xs tabular-nums text-titanium">
                {formatCurrency(amount)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
