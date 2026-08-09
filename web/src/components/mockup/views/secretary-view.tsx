"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Calendar, Mail, MessageSquare } from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { MockCard, StatusBadge } from "../mockup-widgets";
import { poleFadeUp } from "../pole-page-shell";
import { PoleKpiRow, SeeAllLink } from "../pole-kpi-row";
import {
  PoleFilledPanel,
  PoleListCard,
  PoleProtoTabs,
  PoleStatStrip,
} from "../pole-proto-tabs";

interface SecretaryViewProps {
  department: ConsoleDepartment;
}

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "mails", label: "Mails" },
  { id: "agenda", label: "Agenda" },
  { id: "taches", label: "Tâches" },
  { id: "sav", label: "SAV" },
];

const EMAILS = [
  { from: "Investisseur A", subject: "Suite due diligence", time: "10:23", status: "Non lu" },
  { from: "Fournisseur Cloud", subject: "Facture août", time: "09:41", status: "Lu" },
  { from: "Partenaire NUAWAY", subject: "Draft contrat", time: "Hier", status: "À répondre" },
  { from: "Recrutement", subject: "Candidature agent QA", time: "Hier", status: "Non lu" },
];

const MEETINGS = [
  { title: "Stand-up direction", time: "09:00", duration: "30 min" },
  { title: "Review dossiers R&D", time: "11:00", duration: "1h" },
  { title: "Brief CEO comptabilité", time: "14:30", duration: "45 min" },
  { title: "Point marketing campagnes", time: "16:00", duration: "30 min" },
];

const TASKS = [
  { title: "Préparer brief Q3", done: true },
  { title: "Relancer fournisseur cloud", done: false },
  { title: "Classer dossiers CEO", done: false },
  { title: "Réservation salle hebdo", done: true },
];

const SAV = [
  { user: "Client A", issue: "Accès dashboard", status: "Résolu" },
  { user: "Client B", issue: "Export PDF", status: "En cours" },
  { user: "Client C", issue: "Intégration API", status: "En attente" },
];

export function MockupSecretaryView({ department }: SecretaryViewProps) {
  void department;
  const [tab, setTab] = useState("dashboard");
  const back = () => setTab("dashboard");

  return (
    <div className="space-y-3 pb-24">
      <PoleProtoTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "dashboard" ? <SecretaryDashboard onNavigateTab={setTab} /> : null}
      {tab === "mails" ? (
        <PoleFilledPanel title="Boîte mail" subtitle="Priorités & réponses en attente" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Non lus", value: "2" },
              { label: "À répondre", value: "1" },
              { label: "Aujourd'hui", value: "4" },
              { label: "Cette sem.", value: "18" },
              { label: "SLA < 4h", value: "92%" },
            ]}
          />
          <PoleListCard
            title="BOÎTE & SUIVIS"
            rows={[
              ...EMAILS.map((e) => ({
                primary: e.from,
                secondary: e.subject,
                meta: e.status,
                tone: (e.status === "Non lu" || e.status === "À répondre" ? "warn" : "muted") as "warn" | "muted",
              })),
              { primary: "Réponse investisseur A", secondary: "Brouillon — due diligence", meta: "Draft", tone: "warn" },
            ]}
          />
        </PoleFilledPanel>
      ) : null}
      {tab === "agenda" ? (
        <PoleFilledPanel title="Agenda du jour" subtitle="Réunions & créneaux Nadia" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Réunions", value: "4" },
              { label: "Durée totale", value: "2h45" },
              { label: "Libres", value: "3" },
              { label: "Demain", value: "5" },
              { label: "Semaine", value: "18" },
            ]}
          />
          <PoleListCard
            title="AUJOURD'HUI & DEMAIN"
            rows={[
              ...MEETINGS.map((m) => ({
                primary: m.title,
                secondary: m.duration,
                meta: m.time,
                tone: "ok" as const,
              })),
              { primary: "Comité R&D", secondary: "Demain — 1h", meta: "10:00", tone: "muted" },
              { primary: "Point SAV hebdo", secondary: "Demain — 45 min", meta: "16:30", tone: "muted" },
            ]}
          />
        </PoleFilledPanel>
      ) : null}
      {tab === "taches" ? (
        <PoleFilledPanel title="Tâches secrétariat" subtitle="To-do direction & follow-ups" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Ouvertes", value: "2" },
              { label: "Terminées", value: "2" },
              { label: "En retard", value: "0" },
              { label: "Cette sem.", value: "7" },
              { label: "Déléguées", value: "1" },
            ]}
          />
          <PoleListCard
            title="TOUTES LES TÂCHES"
            rows={TASKS.map((t) => ({
              primary: t.title,
              secondary: t.done ? "Validé aujourd'hui" : "Priorité direction",
              meta: t.done ? "Done" : "Ouvert",
              tone: (t.done ? "ok" : "warn") as "ok" | "warn",
            }))}
          />
        </PoleFilledPanel>
      ) : null}
      {tab === "sav" ? (
        <PoleFilledPanel title="SAV / Support" subtitle="Tickets clients & partenaires" onBack={back}>
          <PoleStatStrip
            items={[
              { label: "Ouverts", value: "2" },
              { label: "Résolus", value: "1" },
              { label: "SLA OK", value: "100%" },
              { label: "Temps moy.", value: "6h" },
              { label: "Escalades", value: "0" },
            ]}
          />
          <PoleListCard
            title="TICKETS & FILE"
            rows={[
              ...SAV.map((s) => ({
                primary: `${s.user} — ${s.issue}`,
                secondary: "Canal support",
                meta: s.status,
                tone: (s.status === "Résolu" ? "ok" : s.status === "En cours" ? "warn" : "muted") as
                  | "ok"
                  | "warn"
                  | "muted",
              })),
              { primary: "Client D — Reset MFA", secondary: "Email reçu 13:40", meta: "Nouveau", tone: "warn" },
            ]}
          />
        </PoleFilledPanel>
      ) : null}
    </div>
  );
}

function SecretaryDashboard({ onNavigateTab }: { onNavigateTab: (id: string) => void }) {
  return (
    <div className="space-y-3">
      <PoleKpiRow
        kpis={[
          { label: "MAILS", value: "4", delta: "+2", deltaType: "up", trend: [1, 2, 2, 3, 3, 4], color: "#C08A72", onClick: () => onNavigateTab("mails") },
          { label: "RÉUNIONS", value: "4", delta: "stable", deltaType: "neutral", trend: [4, 4, 4, 4, 4, 4], color: "#60a5fa", onClick: () => onNavigateTab("agenda") },
          { label: "TÂCHES", value: "2", delta: "-1", deltaType: "down", trend: [4, 3, 3, 3, 2, 2], color: "#f97316", onClick: () => onNavigateTab("taches") },
          { label: "TICKETS SAV", value: "3", delta: "+1", deltaType: "up", trend: [1, 1, 2, 2, 2, 3], color: "#22c55e", onClick: () => onNavigateTab("sav") },
        ]}
      />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-3" custom={4} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="NADIA FAURE">
            <div className="flex flex-col items-center gap-2">
              <AgentAvatar agentId="secretary" name="Nadia Faure" size={72} ring />
              <p className="font-title text-base font-semibold text-ivoire">Nadia Faure</p>
              <p className="text-[11px] text-titane/55">Secrétaire de direction</p>
              <StatusBadge status="active">En ligne</StatusBadge>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {["Email", "Réunion", "Tâche", "Note"].map((label) => (
                <button
                  key={label}
                  type="button"
                  className="rounded-lg border border-bronze-faint bg-obsidian/50 px-2 py-2 text-[10px] text-titane/70 hover:text-copper"
                >
                  {label}
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-5" custom={5} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard
            title="MAILS PRIORITAIRES"
            action={<SeeAllLink onClick={() => onNavigateTab("mails")} label="Boîte" />}
          >
            <div className="space-y-2">
              {EMAILS.map((e) => (
                <button
                  key={e.subject}
                  type="button"
                  onClick={() => onNavigateTab("mails")}
                  className="w-full rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2 text-left transition-all hover:border-copper/40"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-[11px] font-medium text-ivoire/90">{e.from}</p>
                    <span className="text-[10px] text-titane/50">{e.time}</span>
                  </div>
                  <p className="text-[11px] text-titane/65">{e.subject}</p>
                  <div className="mt-1">
                    <StatusBadge
                      status={e.status === "Non lu" ? "active" : e.status === "À répondre" ? "warning" : "neutral"}
                    >
                      {e.status}
                    </StatusBadge>
                  </div>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-4" custom={6} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="AGENDA DU JOUR" action={<Calendar className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2">
              {MEETINGS.map((m) => (
                <button
                  key={m.title}
                  type="button"
                  onClick={() => onNavigateTab("agenda")}
                  className="flex w-full items-center gap-3 rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2 text-left hover:border-copper/40"
                >
                  <div className="text-center">
                    <p className="font-title text-sm font-semibold text-copper">{m.time}</p>
                    <p className="text-[9px] text-titane/50">{m.duration}</p>
                  </div>
                  <p className="text-[11px] text-ivoire/80">{m.title}</p>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-6" custom={7} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="TÂCHES SECRÉTARIAT" action={<SeeAllLink onClick={() => onNavigateTab("taches")} label="Toutes" />}>
            <div className="space-y-2">
              {TASKS.map((t) => (
                <div
                  key={t.title}
                  className="flex items-center gap-2 rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2"
                >
                  <div
                    className={`h-3 w-3 rounded-full border ${t.done ? "border-online bg-online" : "border-titane/40"}`}
                  />
                  <span
                    className={
                      t.done ? "text-[11px] text-titane/50 line-through" : "text-[11px] text-ivoire/80"
                    }
                  >
                    {t.title}
                  </span>
                </div>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-6" custom={8} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="SAV / SUPPORT" action={<MessageSquare className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2">
              {SAV.map((s) => (
                <button
                  key={s.user}
                  type="button"
                  onClick={() => onNavigateTab("sav")}
                  className="flex w-full items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2 text-left hover:border-copper/40"
                >
                  <div>
                    <p className="text-[11px] text-ivoire/80">{s.user}</p>
                    <p className="text-[10px] text-titane/50">{s.issue}</p>
                  </div>
                  <StatusBadge
                    status={s.status === "Résolu" ? "success" : s.status === "En cours" ? "active" : "warning"}
                  >
                    {s.status}
                  </StatusBadge>
                </button>
              ))}
            </div>
            <button type="button" onClick={() => onNavigateTab("sav")} className="mt-2 text-[10px] text-copper hover:underline">
              Voir tous les tickets →
            </button>
          </MockCard>
        </motion.div>
      </div>

      <motion.div custom={9} variants={poleFadeUp} initial="hidden" animate="show">
        <MockCard title="DOCUMENTS RÉCENTS" action={<Mail className="h-3.5 w-3.5 text-copper/70" />}>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {["Brief Q3.pdf", "Contrat NUAWAY.docx", "Org chart 2026.fig", "Roadmap v2.md"].map((doc) => (
              <div
                key={doc}
                className="rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2 text-[11px] text-ivoire/80"
              >
                {doc}
              </div>
            ))}
          </div>
        </MockCard>
      </motion.div>
    </div>
  );
}
