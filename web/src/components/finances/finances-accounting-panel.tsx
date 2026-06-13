"use client";

import { AgentActionConsole } from "@/components/shared/agent-action-console";
import { accountingFinancialAdvice } from "@/lib/pole-api";

interface FinancesAccountingPanelProps {
  month: string;
  dashboardData?: {
    total_income: number;
    total_expenses: number;
    balance: number;
    by_category?: Record<string, number>;
  };
}

export function FinancesAccountingPanel({
  month,
  dashboardData,
}: FinancesAccountingPanelProps) {
  const summary = {
    revenus: dashboardData?.total_income ?? 0,
    depenses: dashboardData?.total_expenses ?? 0,
    solde: dashboardData?.balance ?? 0,
    par_categorie: dashboardData?.by_category ?? {},
  };

  return (
    <section className="space-y-4">
      <h2 className="label-caps">Jules — Comptabilité</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <AgentActionConsole
          title="Conseil sur la période"
          description={`Analyse comptable — ${month}`}
          fields={[
            {
              name: "question",
              label: "Ta question",
              type: "textarea",
              required: true,
              rows: 3,
              placeholder: "Est-ce que je peux me payer un salaire ce mois-ci ?",
            },
          ]}
          onSubmit={(v) =>
            accountingFinancialAdvice({
              month,
              financial_summary: summary,
              question: v.question,
            })
          }
        />
        <AgentActionConsole
          title="Vérifier la trésorerie"
          description="Diagnostic rapide solde + charges"
          fields={[
            {
              name: "question",
              label: "Contexte (optionnel)",
              type: "textarea",
              rows: 2,
              placeholder: "Gros achat matériel prévu, baisse de revenus…",
              defaultValue:
                "Analyse ma trésorerie et dis-moi si je dois reporter des dépenses.",
            },
          ]}
          onSubmit={(v) =>
            accountingFinancialAdvice({
              month,
              financial_summary: summary,
              question:
                v.question ||
                "Analyse ma trésorerie et signale les risques pour une fondatrice solo.",
            })
          }
        />
      </div>
    </section>
  );
}
