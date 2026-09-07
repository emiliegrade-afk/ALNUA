"use client";

import Link from "next/link";
import {
  Bell,
  CalendarPlus,
  FilePlus2,
  Mail,
  Scale,
} from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { SiegeLifeLinks } from "@/components/shared/siege-life-links";
import {
  SiegeBadge,
  SiegePageHeader,
  SiegePanel,
  SiegeQuickLink,
} from "@/components/siege/siege-ui";
import { ROUTES } from "@/lib/routes";

const AGENDA = [
  { time: "09:00", title: "Réunion Direction", who: "Aria · Sam" },
  { time: "11:00", title: "Tri courrier & contrats", who: "Nadia" },
  { time: "14:30", title: "Escalade Solène (NDA)", who: "Legal" },
  { time: "16:00", title: "Relances partenaires", who: "Nadia" },
] as const;

const TASKS = [
  {
    title: "Relire contrat NDA ALNUA",
    agentId: "legal_counsel",
    agent: "Solène",
    priority: "Haute" as const,
  },
  {
    title: "Agenda CEO — créneaux semaine",
    agentId: "secretary",
    agent: "Nadia",
    priority: "Haute" as const,
  },
  {
    title: "Scan ménage PC (Clara)",
    agentId: "housekeeper",
    agent: "Clara",
    priority: "Moyenne" as const,
  },
  {
    title: "Exporter docs Word dossier",
    agentId: "secretary",
    agent: "Nadia",
    priority: "Moyenne" as const,
  },
] as const;

const MAIL = [
  { from: "Partenaire UE", subject: "Signature NDA", when: "09:12" },
  { from: "Aria Voss", subject: "Priorités COO du jour", when: "08:40" },
  { from: "Comms", subject: "Calendrier posts", when: "Hier" },
] as const;

const DOCS = [
  { name: "NDA-ALNUA.docx", when: "il y a 2 h" },
  { name: "Agenda-Direction.pdf", when: "hier" },
  { name: "Brief-CEO.txt", when: "hier" },
] as const;

const ROOMS = [
  { room: "Salle Orion", slot: "10:00–11:30", who: "Direction" },
  { room: "Lab R&D", slot: "14:00–15:00", who: "Comité" },
] as const;

const REMINDERS = [
  { text: "Relance signature NDA", tone: "danger" as const, tag: "Urgent" },
  { text: "Préparer pack Solène", tone: "copper" as const, tag: "Moyen" },
  { text: "Sync Clara ménage", tone: "muted" as const, tag: "Bas" },
] as const;

/** Secrétariat — layout maquette, couleurs ALNUA. */
export function SecretaryCommandView() {
  return (
    <div className="flex flex-col gap-4">
      <SiegePageHeader
        title="SECRÉTARIAT"
        accent="NADIA"
        subtitle="Agenda · tâches · courrier · documents · escalade Solène"
        trailing={<SiegeLifeLinks />}
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <SiegePanel title="Agenda du jour">
          <ul className="relative space-y-0 border-l border-copper/25 pl-4">
            {AGENDA.map((a) => (
              <li key={a.time} className="relative pb-4 last:pb-0">
                <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full border border-copper bg-obsidian" />
                <p className="font-mono text-[11px] text-copper">{a.time}</p>
                <p className="text-[13px] text-ivory">{a.title}</p>
                <p className="text-[11px] text-titanium/55">{a.who}</p>
              </li>
            ))}
          </ul>
        </SiegePanel>

        <SiegePanel
          title="Tâches en cours"
          action={
            <Link href={ROUTES.legal} className="text-[10px] text-copper hover:underline">
              Solène →
            </Link>
          }
        >
          <ul className="space-y-3">
            {TASKS.map((t) => (
              <li key={t.title} className="flex items-center gap-3">
                <AgentAvatar agentId={t.agentId} name={t.agent} size={36} ring />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[12px] text-ivory">{t.title}</p>
                  <p className="text-[10px] text-titanium/55">{t.agent}</p>
                </div>
                <SiegeBadge tone={t.priority === "Haute" ? "copper" : "muted"}>
                  {t.priority}
                </SiegeBadge>
              </li>
            ))}
          </ul>
        </SiegePanel>

        <SiegePanel title="Courrier">
          <ul className="space-y-3">
            {MAIL.map((m) => (
              <li key={m.subject} className="flex items-start gap-2 border-b border-titanium/10 pb-2 last:border-0 last:pb-0">
                <Mail className="mt-0.5 h-3.5 w-3.5 shrink-0 text-copper/70" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[12px] text-ivory">{m.subject}</p>
                  <p className="text-[10px] text-titanium/55">{m.from}</p>
                </div>
                <span className="shrink-0 text-[10px] text-titanium/45">{m.when}</span>
              </li>
            ))}
          </ul>
        </SiegePanel>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <SiegePanel title="Documents récents">
          <ul className="space-y-2">
            {DOCS.map((d) => (
              <li key={d.name} className="flex items-center justify-between gap-2 text-[12px]">
                <span className="truncate text-ivory/90">{d.name}</span>
                <span className="shrink-0 text-[10px] text-titanium/50">{d.when}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-[11px] text-titanium/50">
            Docs & contrats Word → panneau outils ci-dessous
          </p>
        </SiegePanel>

        <SiegePanel title="Réservations">
          <ul className="space-y-2.5">
            {ROOMS.map((r) => (
              <li key={r.room} className="text-[12px]">
                <p className="text-ivory">{r.room}</p>
                <p className="text-[11px] text-copper/80">{r.slot}</p>
                <p className="text-[10px] text-titanium/50">{r.who}</p>
              </li>
            ))}
          </ul>
        </SiegePanel>

        <SiegePanel title="Rappels & relances">
          <ul className="space-y-2.5">
            {REMINDERS.map((r) => (
              <li key={r.text} className="flex items-center justify-between gap-2 text-[12px] text-ivory/85">
                <span className="min-w-0 truncate">{r.text}</span>
                <SiegeBadge tone={r.tone}>{r.tag}</SiegeBadge>
              </li>
            ))}
          </ul>
        </SiegePanel>
      </div>

      <div className="flex flex-wrap gap-2">
        <SiegeQuickLink href={ROUTES.secretary} label="Nouveau document" icon={<FilePlus2 className="h-3.5 w-3.5" />} />
        <SiegeQuickLink href={ROUTES.briefing} label="Planifier réunion" icon={<CalendarPlus className="h-3.5 w-3.5" />} />
        <SiegeQuickLink href={ROUTES.legal} label="Escalade Solène" icon={<Scale className="h-3.5 w-3.5" />} />
        <SiegeQuickLink href={ROUTES.lounge} label="Agent Lounge" icon={<Bell className="h-3.5 w-3.5" />} />
      </div>
    </div>
  );
}
