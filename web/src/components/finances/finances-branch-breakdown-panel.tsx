"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchFinanceTransactions, formatCurrency, type FinanceTransaction } from "@/lib/finances-api";
import type { Project } from "@/lib/types";
import { C, Bar } from "@/app/app-v2/shared";

/* "Dépenses par branche produit" — Vue Globale Finance (redesign). PAS "par
   département" : projects.branch n'a que 4 valeurs réelles
   (app/gaming/robotics/other, database/schema.sql) — pas les 9-10 pôles.
   Le bucket "Sans projet" (dépenses générales ALNUA, pas liées à un projet)
   n'est jamais masqué — c'est probablement le plus gros poste. */

const BRANCH_LABELS: Record<string, string> = {
  app: "App",
  gaming: "Gaming",
  robotics: "Robotique",
  other: "Autre",
  none: "Sans projet (dépense générale)",
};

export function FinancesBranchBreakdownPanel({ month, projects }: { month: string; projects: Project[] }) {
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
      const branch = tx.project_id ? projectById.get(tx.project_id)?.branch ?? "other" : "none";
      totals[branch] = (totals[branch] ?? 0) + tx.amount;
    }
    const max = Math.max(1, ...Object.values(totals));
    return Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .map(([branch, amount]) => ({ branch, amount, pct: Math.round((amount / max) * 100) }));
  }, [transactions, projects]);

  return (
    <div className="rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
      <p className="text-[10.5px]" style={{ color: "#D8CFC4" }}>
        Dépenses par branche produit
      </p>
      <p className="mt-0.5 text-[8.5px]" style={{ color: C.faint }}>
        Basé sur les transactions liées à un projet.
      </p>
      {loading && transactions.length === 0 ? (
        <p className="mt-3 text-[9.5px]" style={{ color: C.faint }}>
          Chargement…
        </p>
      ) : byBranch.length === 0 ? (
        <p className="mt-3 text-[9.5px]" style={{ color: C.faint }}>
          Aucune dépense ce mois-ci.
        </p>
      ) : (
        <div className="mt-2.5 flex flex-col gap-2">
          {byBranch.map(({ branch, amount, pct }) => (
            <div key={branch} className="flex items-center gap-2">
              <span className="w-[130px] shrink-0 truncate text-[10px]" style={{ color: C.warm }}>
                {BRANCH_LABELS[branch] ?? branch}
              </span>
              <Bar value={pct} thick={4} />
              <span className="w-[62px] shrink-0 text-right text-[10px]" style={{ color: "#E8DFD4" }}>
                {formatCurrency(amount)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
