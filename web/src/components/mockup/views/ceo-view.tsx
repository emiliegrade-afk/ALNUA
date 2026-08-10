"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Crown, ExternalLink, FileText, Scale, TrendingUp } from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { cn } from "@/lib/utils";
import { MockCard, ProgressBar, StatusBadge } from "../mockup-widgets";
import { poleFadeUp } from "../pole-page-shell";
import { PoleKpiRow, SeeAllLink } from "../pole-kpi-row";
import {
  PoleFilledPanel,
  PoleListCard,
  PoleProtoTabs,
  PoleStatStrip,
} from "../pole-proto-tabs";

interface CeoViewProps {
  department: ConsoleDepartment;
}

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "decisions", label: "Décisions" },
  { id: "briefs", label: "Briefs" },
  { id: "prs", label: "PRs" },
  { id: "okr", label: "OKR" },
];

const DOSSIERS = [
  { title: "Lancer le MVP NOMAD", score: 86, status: "GO" },
  { title: "Campagne Ads été 2026", score: 74, status: "Maybe" },
  { title: "Acquisition outil CRM", score: 42, status: "No" },
];

const PRS = [
  { number: 142, title: "Auth SSO multi-produits" },
  { number: 141, title: "Refactor stores ALNUA" },
  { number: 138, title: "Pipeline CI/CD gaming" },
];

const DECISIONS = [
  { title: "Validation budget Q3", status: "En attente", deadline: "10 août" },
  { title: "Choix moteur EVE v2", status: "En attente", deadline: "15 août" },
  { title: "Recrutement agent QA", status: "Approuvé", deadline: "—" },
];

export function MockupCeoView({ department }: CeoViewProps) {
  const [tab, setTab] = useState("dashboard");
  const back = () => setTab("dashboard");

  return (
    <div className="space-y-3 pb-24">
      <PoleProtoTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "dashboard" ? <CeoDashboard department={department} onNavigateTab={setTab} /> : null}
      {tab === "decisions" ? (
        <PoleFilledPanel title="Pipeline décisions" subtitle="GO / Maybe / No — validation CEO" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "En attente", value: "2" },
              { label: "GO", value: "8" },
              { label: "Maybe", value: "3" },
              { label: "No", value: "1" },
              { label: "Score moyen", value: "74%" },
            ]}
          />
          <PoleListCard
            title="DOSSIERS & ÉCHÉANCES"
            rows={[
              ...DOSSIERS.map((d) => ({
                primary: d.title,
                secondary: `Score ${d.score}%`,
                meta: d.status,
                tone: (d.status === "GO" ? "ok" : d.status === "Maybe" ? "warn" : "muted") as "ok" | "warn" | "muted",
              })),
              ...DECISIONS.map((d) => ({
                primary: d.title,
                secondary: d.deadline === "—" ? "Sans deadline" : `Deadline ${d.deadline}`,
                meta: d.status,
                tone: (d.status === "Approuvé" ? "ok" : "warn") as "ok" | "warn",
              })),
            ]}
          />
        </PoleFilledPanel>
      ) : null}
      {tab === "briefs" ? (
        <PoleFilledPanel title="Briefs exécutifs" subtitle="Synthèses quotidiennes & hebdo" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Briefs / mois", value: "12" },
              { label: "Ouverts", value: "3" },
              { label: "Archivés", value: "9" },
              { label: "Priorités Q3", value: "4" },
              { label: "Alertes", value: "1" },
            ]}
          />
          <PoleListCard
            title="BRIEF DU JOUR & HISTORIQUE"
            rows={[
              { primary: "Stabiliser la console", secondary: "Priorité Q3 — ops", meta: "P0", tone: "warn" },
              { primary: "MVP NOMAD septembre", secondary: "Livraison produit", meta: "P1", tone: "ok" },
              { primary: "Burn rate marketing", secondary: "Surveillance coûts", meta: "Watch", tone: "warn" },
              { primary: "Brief 8 août", secondary: "Direction + R&D", meta: "Lu", tone: "muted" },
              { primary: "Brief hebdo S31", secondary: "Tous pôles", meta: "Archivé", tone: "muted" },
            ]}
          />
        </PoleFilledPanel>
      ) : null}
      {tab === "prs" ? (
        <PoleFilledPanel title="Pull requests" subtitle="Revue code cross-produits" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "En review", value: "3" },
              { label: "Revus / mois", value: "24" },
              { label: "Mergés", value: "18" },
              { label: "Bloqués", value: "1" },
              { label: "Temps moyen", value: "1.4j" },
            ]}
          />
          <PoleListCard
            title="REVIEW & MERGES"
            rows={[
              ...PRS.map((pr) => ({
                primary: `#${pr.number} — ${pr.title}`,
                secondary: "alnua-hub",
                meta: "Review",
                tone: "warn" as const,
              })),
              { primary: "#137 — Fix auth middleware", secondary: "alnua-hub", meta: "Merged", tone: "ok" },
              { primary: "#135 — Dashboard coûts LLM", secondary: "alnua-core", meta: "Merged", tone: "ok" },
            ]}
          />
        </PoleFilledPanel>
      ) : null}
      {tab === "okr" ? (
        <PoleFilledPanel title="OKR Q3" subtitle="Objectifs & résultats clés direction" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Confiance", value: "87%" },
              { label: "Avancement", value: "62%" },
              { label: "Dette tech", value: "34%" },
              { label: "KR verts", value: "5" },
              { label: "KR à risque", value: "2" },
            ]}
          />
          <PoleListCard
            title="OBJECTIFS & KR"
            rows={[
              { primary: "O1 — Console opérationnelle", secondary: "Uptime & adoption", meta: "78%", tone: "ok" },
              { primary: "O2 — Ship NOMAD MVP", secondary: "Septembre 2026", meta: "55%", tone: "warn" },
              { primary: "O3 — Pipeline QA solide", secondary: "Coverage + recrutement", meta: "70%", tone: "ok" },
              { primary: "KR — Burn LLM < 500$", secondary: "Budget mensuel", meta: "Risque", tone: "warn" },
            ]}
          />
        </PoleFilledPanel>
      ) : null}
    </div>
  );
}

function CeoDashboard({
  department,
  onNavigateTab,
}: {
  department: ConsoleDepartment;
  onNavigateTab: (id: string) => void;
}) {
  return (
    <div className="space-y-3">
      <PoleKpiRow
        kpis={[
          { label: "DÉCISIONS", value: "3", delta: "-1", deltaType: "down", trend: [5, 5, 4, 4, 3, 3], color: "#f97316", onClick: () => onNavigateTab("decisions") },
          { label: "BRIEFS", value: "12", delta: "+3", deltaType: "up", trend: [8, 9, 10, 10, 11, 12], color: "#E09B6A", onClick: () => onNavigateTab("briefs") },
          { label: "DOSSIERS GO", value: "8", delta: "+2", deltaType: "up", trend: [4, 5, 6, 6, 7, 8], color: "#22c55e", onClick: () => onNavigateTab("decisions") },
          { label: "PRs REVUS", value: "24", delta: "+6", deltaType: "up", trend: [15, 17, 18, 20, 21, 24], color: "#60a5fa", onClick: () => onNavigateTab("prs") },
        ]}
      />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-7" custom={4} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="DOSSIERS GO / MAYBE / NO" action={<Scale className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2.5">
              {DOSSIERS.map((d) => (
                <button
                  key={d.title}
                  type="button"
                  onClick={() => onNavigateTab("decisions")}
                  className="flex w-full items-start justify-between rounded-xl border border-bronze-faint bg-obsidian/50 p-3 text-left transition-all hover:border-copper/40"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-[12px] font-medium text-ivoire/90">{d.title}</p>
                    <div className="mt-2">
                      <ProgressBar value={d.score} />
                    </div>
                  </div>
                  <span
                    className={cn(
                      "ml-3 shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium",
                      d.status === "GO" && "bg-online/10 text-online",
                      d.status === "No" && "bg-red-400/10 text-red-400",
                      d.status === "Maybe" && "bg-copper/10 text-copper",
                    )}
                  >
                    {d.score}% {d.status}
                  </span>
                </button>
              ))}
            </div>
            <SeeAllLink onClick={() => onNavigateTab("decisions")} label="Pipeline décisions" />
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-5 space-y-3" custom={5} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="BRIEF DU JOUR" action={<FileText className="h-3.5 w-3.5 text-copper/70" />}>
            <p className="text-[11px] leading-relaxed text-ivoire/85">
              Priorité Q3 : stabiliser la console, lancer le MVP NOMAD en septembre, et renforcer le pipeline QA.
              Surveiller le burn rate marketing.
            </p>
            <div className="mt-2 space-y-1">
              <p className="text-[10px] text-copper">• Validation budget Q3</p>
              <p className="text-[10px] text-copper">• Choix moteur EVE v2</p>
              <p className="text-[10px] text-titane/55">• Recrutement agent QA — approuvé</p>
            </div>
            <button type="button" onClick={() => onNavigateTab("briefs")} className="mt-2 text-[10px] text-copper hover:underline">
              Historique briefs →
            </button>
          </MockCard>

          <MockCard title="OKR Q3" action={<Crown className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2">
              <OkrRow label="Confiance globale" value={87} />
              <OkrRow label="Avancement OKR" value={62} />
              <OkrRow label="Dette technique" value={34} invert />
            </div>
            <button type="button" onClick={() => onNavigateTab("okr")} className="mt-2 w-full text-[10px] text-copper hover:underline">
              Détail OKR →
            </button>
          </MockCard>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-4" custom={6} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="PRs EN ATTENTE" action={<ExternalLink className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2">
              {PRS.map((pr) => (
                <button
                  key={pr.number}
                  type="button"
                  onClick={() => onNavigateTab("prs")}
                  className="flex w-full items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2 text-left hover:border-copper/40"
                >
                  <span className="text-[11px] text-ivoire/80">
                    #{pr.number} — {pr.title}
                  </span>
                  <span className="text-[10px] text-copper">Review</span>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-4" custom={7} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="PIPELINE DÉCISIONS">
            <div className="space-y-2">
              {DECISIONS.map((d) => (
                <div key={d.title} className="rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2">
                  <p className="text-[11px] font-medium text-ivoire/90">{d.title}</p>
                  <div className="mt-1 flex items-center justify-between">
                    <StatusBadge status={d.status === "Approuvé" ? "success" : "active"}>{d.status}</StatusBadge>
                    <span className="text-[10px] text-titane/50">{d.deadline}</span>
                  </div>
                </div>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-4" custom={8} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="ÉQUIPE CEO" action={<TrendingUp className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2">
              {department.agents.map((a) => (
                <div key={a.id} className="flex items-center gap-2">
                  <AgentAvatar agentId={a.id} name={a.name} size={32} />
                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] font-medium text-ivoire/90">{a.name}</p>
                    <p className="text-[9px] text-titane/55">{a.role}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 space-y-1.5 border-t border-bronze-faint pt-2">
              <TrendRow label="Coûts LLM" value="+12%" positive={false} />
              <TrendRow label="Vitesse delivery" value="+24%" positive />
            </div>
          </MockCard>
        </motion.div>
      </div>
    </div>
  );
}

function OkrRow({ label, value, invert }: { label: string; value: number; invert?: boolean }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-[10px]">
        <span className="text-titane/60">{label}</span>
        <span className={invert ? "text-orange-400" : "text-copper"}>{value}%</span>
      </div>
      <ProgressBar value={value} />
    </div>
  );
}

function TrendRow({ label, value, positive }: { label: string; value: string; positive: boolean }) {
  return (
    <div className="flex items-center justify-between text-[10px]">
      <span className="text-ivoire/80">{label}</span>
      <span className={positive ? "text-online" : "text-red-400"}>{value}</span>
    </div>
  );
}
