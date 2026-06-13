"use client";

import { AgentActionConsole } from "@/components/shared/agent-action-console";
import {
  analystBusinessBrief,
  analystBusinessKpis,
  analystBusinessMarket,
  analystBusinessUserResearch,
  analystDataAnomaly,
  analystDataDashboard,
  analystDataFunnel,
  analystDataSql,
} from "@/lib/pole-api";

export function AnalyticsAgentsPanel() {
  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <h2 className="label-caps">Layla — Analyse business</h2>
        <div className="grid gap-4 lg:grid-cols-2">
          <AgentActionConsole
            title="Analyse de marché"
            fields={[
              { name: "product", label: "Produit", required: true, placeholder: "Naïa" },
              { name: "market", label: "Marché cible", required: true, placeholder: "Vanlife FR" },
              {
                name: "competitors",
                label: "Concurrents (virgules)",
                placeholder: "Nomad, Vanly…",
              },
            ]}
            onSubmit={(v) =>
              analystBusinessMarket({
                product: v.product,
                market: v.market,
                competitors: v.competitors
                  ? v.competitors.split(",").map((c) => c.trim()).filter(Boolean)
                  : undefined,
              })
            }
          />
          <AgentActionConsole
            title="Définir les KPIs"
            fields={[
              { name: "project", label: "Projet", required: true },
              {
                name: "stage",
                label: "Stade",
                type: "select",
                defaultValue: "beta",
                options: [
                  { value: "ideation", label: "Idéation" },
                  { value: "mvp", label: "MVP" },
                  { value: "beta", label: "Bêta" },
                  { value: "growth", label: "Croissance" },
                ],
              },
              {
                name: "business_goal",
                label: "Objectif business",
                type: "textarea",
                required: true,
                rows: 2,
              },
            ]}
            onSubmit={(v) =>
              analystBusinessKpis({
                project: v.project,
                stage: v.stage,
                business_goal: v.business_goal,
              })
            }
          />
          <AgentActionConsole
            title="Recherche utilisateurs"
            fields={[
              { name: "product", label: "Produit", required: true },
              {
                name: "research_question",
                label: "Question de recherche",
                type: "textarea",
                required: true,
                rows: 2,
              },
              { name: "user_segment", label: "Segment utilisateur", placeholder: "Vanlifers 25-40 ans" },
            ]}
            onSubmit={(v) =>
              analystBusinessUserResearch({
                product: v.product,
                research_question: v.research_question,
                user_segment: v.user_segment,
              })
            }
          />
          <AgentActionConsole
            title="Note stratégique"
            fields={[
              { name: "topic", label: "Sujet", required: true },
              {
                name: "context",
                label: "Contexte",
                type: "textarea",
                required: true,
                rows: 3,
              },
              {
                name: "decision_needed",
                label: "Décision attendue",
                required: true,
                placeholder: "Lancer ou reporter la feature X ?",
              },
            ]}
            onSubmit={(v) =>
              analystBusinessBrief({
                topic: v.topic,
                context: v.context,
                decision_needed: v.decision_needed,
              })
            }
          />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="label-caps">Axel — Data & BI</h2>
        <div className="grid gap-4 lg:grid-cols-2">
          <AgentActionConsole
            title="Requête SQL"
            fields={[
              {
                name: "question",
                label: "Question en français",
                type: "textarea",
                required: true,
                rows: 2,
                placeholder: "Combien d'inscriptions waitlist ce mois ?",
              },
              {
                name: "schema_context",
                label: "Tables / colonnes connues",
                type: "textarea",
                rows: 3,
                placeholder: "waitlist_signups(email, project_slug, created_at)",
              },
            ]}
            onSubmit={(v) =>
              analystDataSql({
                question: v.question,
                schema_context: v.schema_context || "Supabase PostgreSQL ALNUA",
              })
            }
          />
          <AgentActionConsole
            title="Analyse entonnoir"
            fields={[
              { name: "funnel_name", label: "Nom de l'entonnoir", required: true },
              {
                name: "steps",
                label: "Étapes (une par ligne)",
                type: "textarea",
                required: true,
                rows: 3,
                placeholder: "Visite\nInscription\nActivation",
              },
              {
                name: "data",
                label: "Données (JSON)",
                type: "textarea",
                rows: 3,
                placeholder: '{"visite": 1000, "inscription": 120}',
              },
            ]}
            onSubmit={async (v) => {
              let data: Record<string, unknown> = {};
              if (v.data?.trim()) {
                try {
                  data = JSON.parse(v.data) as Record<string, unknown>;
                } catch {
                  throw new Error("JSON invalide dans le champ données");
                }
              }
              return analystDataFunnel({
                funnel_name: v.funnel_name,
                steps: v.steps.split("\n").map((s) => s.trim()).filter(Boolean),
                data,
              });
            }}
          />
          <AgentActionConsole
            title="Détecter une anomalie"
            fields={[
              { name: "metric", label: "Métrique", required: true, placeholder: "DAU" },
              {
                name: "recent_values",
                label: "Valeurs récentes (virgules)",
                required: true,
                placeholder: "120, 118, 45, 122",
              },
              { name: "baseline", label: "Référence", defaultValue: "moyenne 7j" },
              { name: "period", label: "Période", defaultValue: "7 derniers jours" },
            ]}
            onSubmit={(v) =>
              analystDataAnomaly({
                metric: v.metric,
                recent_values: v.recent_values
                  .split(",")
                  .map((n) => parseFloat(n.trim()))
                  .filter((n) => !Number.isNaN(n)),
                baseline: v.baseline,
                period: v.period,
              })
            }
          />
          <AgentActionConsole
            title="Spécifier un tableau de bord"
            fields={[
              { name: "dashboard_name", label: "Nom du dashboard", required: true },
              { name: "audience", label: "Public", defaultValue: "Emilie / CEO" },
              {
                name: "kpis",
                label: "KPIs (virgules)",
                required: true,
                placeholder: "MRR, rétention, NPS",
              },
              {
                name: "data_sources",
                label: "Sources de données (virgules)",
                placeholder: "Supabase, Stripe, Plausible",
              },
            ]}
            onSubmit={(v) =>
              analystDataDashboard({
                dashboard_name: v.dashboard_name,
                audience: v.audience,
                kpis: v.kpis.split(",").map((k) => k.trim()).filter(Boolean),
                data_sources: v.data_sources
                  ? v.data_sources.split(",").map((s) => s.trim()).filter(Boolean)
                  : ["Supabase"],
              })
            }
          />
        </div>
      </section>
    </div>
  );
}
