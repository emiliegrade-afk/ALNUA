"use client";

import { AgentActionConsole } from "@/components/shared/agent-action-console";
import {
  controllerAnalyzeCosts,
  controllerForecast,
  controllerLlmAlert,
  controllerMonthlyReport,
} from "@/lib/pole-api";

interface FinancesControllerPanelProps {
  month: string;
  dashboardData?: {
    total_income: number;
    total_expenses: number;
    balance: number;
    by_category?: Record<string, number>;
  };
}

export function FinancesControllerPanel({
  month,
  dashboardData,
}: FinancesControllerPanelProps) {
  const costsPayload = {
    income: dashboardData?.total_income ?? 0,
    expenses: dashboardData?.total_expenses ?? 0,
    balance: dashboardData?.balance ?? 0,
    by_category: dashboardData?.by_category ?? {},
  };

  return (
    <section className="space-y-4">
      <h2 className="label-caps">Rémi — Contrôle de gestion</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <AgentActionConsole
          title="Analyse des coûts"
          description={`Période : ${month}`}
          fields={[
            {
              name: "budget",
              label: "Budget mensuel (€)",
              type: "number",
              placeholder: "2000",
            },
          ]}
          onSubmit={(v) =>
            controllerAnalyzeCosts({
              period: month,
              costs_data: costsPayload,
              budget: v.budget
                ? { monthly: parseFloat(v.budget) }
                : undefined,
            })
          }
        />
        <AgentActionConsole
          title="Prévision financière"
          fields={[
            { name: "project", label: "Projet", defaultValue: "ALNUA global", required: true },
            {
              name: "assumptions",
              label: "Hypothèses",
              type: "textarea",
              required: true,
              rows: 3,
              placeholder: "Croissance Naïa +20%, coûts LLM stables…",
            },
            {
              name: "horizon_months",
              label: "Horizon (mois)",
              type: "number",
              defaultValue: "6",
            },
          ]}
          onSubmit={(v) =>
            controllerForecast({
              project: v.project,
              assumptions: v.assumptions,
              horizon_months: parseInt(v.horizon_months, 10) || 6,
              historical_data: costsPayload,
            })
          }
        />
        <AgentActionConsole
          title="Alerte coûts LLM"
          fields={[
            {
              name: "daily_spend",
              label: "Dépense du jour ($)",
              type: "number",
              required: true,
            },
            {
              name: "monthly_budget",
              label: "Budget mensuel LLM ($)",
              type: "number",
              required: true,
              defaultValue: "50",
            },
          ]}
          onSubmit={(v) =>
            controllerLlmAlert({
              daily_spend: parseFloat(v.daily_spend),
              monthly_budget: parseFloat(v.monthly_budget),
            })
          }
        />
        <AgentActionConsole
          title="Rapport mensuel"
          fields={[
            {
              name: "notes",
              label: "Notes additionnelles",
              type: "textarea",
              rows: 2,
            },
          ]}
          onSubmit={(v) =>
            controllerMonthlyReport({
              month,
              all_data: { ...costsPayload, notes: v.notes },
            })
          }
        />
      </div>
    </section>
  );
}
