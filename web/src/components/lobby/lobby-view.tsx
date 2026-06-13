"use client";

import { useEffect, useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { Bell } from "lucide-react";
import Link from "next/link";
import { AlnuaLogo } from "@/components/brand/alnua-logo";
import { DepartmentDoor } from "@/components/lobby/department-door";
import { DEPT_TIERS } from "@/lib/dept-colors";
import { countAgentsForBureau } from "@/lib/agent-bureau";
import { fetchLobbyStats, type LobbyStats } from "@/lib/lobby-api";
import {
  countActiveAgents,
  fetchAgentsStatus,
} from "@/lib/openroom-api";
import { cn } from "@/lib/utils";

const DEFAULT_STATS: LobbyStats = {
  apiOnline: false,
  apiAuthenticated: false,
  ceoNotifications: 0,
  hubPrCount: 0,
  appOpenTickets: 0,
  gamingStatus: "Wyrdheim R&D en cours",
  roboStatus: "Eve — Prototype",
  financesMonthTotal: "$0.00",
  marketingPendingPosts: 0,
  rdSessions: 0,
  brandKits: 0,
  connectedApps: 0,
};

export function LobbyView() {
  const [stats, setStats] = useState<LobbyStats>(DEFAULT_STATS);
  const [activeAgents, setActiveAgents] = useState(0);
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    fetchLobbyStats()
      .then(setStats)
      .catch(() => setStats(DEFAULT_STATS));

    fetchAgentsStatus()
      .then((data) => setActiveAgents(countActiveAgents(data.agents)))
      .catch(() => setActiveAgents(0));

    const clock = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(clock);
  }, []);

  const doors = [
    {
      icon: "🏢",
      title: "OpenRoom",
      subtitle: "War room · Agents live",
      description: "Vue temps réel",
      href: "/openroom",
      tier: DEPT_TIERS.hub,
      badge:
        activeAgents > 0
          ? `${activeAgents} actif${activeAgents > 1 ? "s" : ""}`
          : "War room",
      stats:
        activeAgents > 0
          ? `${activeAgents} agent${activeAgents > 1 ? "s" : ""} en activité`
          : "Tous les agents au repos",
    },
    {
      icon: "👑",
      title: "Bureau du CEO",
      subtitle: "Mission Control · Brief · Décisions en attente",
      description: "CEO · Emilie",
      href: "/ceo",
      tier: DEPT_TIERS.ceo,
      badge:
        stats.ceoNotifications > 0
          ? `${stats.ceoNotifications} notif${stats.ceoNotifications > 1 ? "s" : ""}`
          : "CEO",
      stats: `Brief & décisions · ${stats.ceoNotifications} notification${stats.ceoNotifications !== 1 ? "s" : ""}`,
    },
    {
      icon: "📎",
      title: "Secrétariat",
      subtitle: "Nadia Faure · Emails · Agenda · Contrats",
      description: `${countAgentsForBureau("secretary")} Agent`,
      href: "/secretary",
      tier: DEPT_TIERS.secretary,
      badge: `${countAgentsForBureau("secretary")} Agent`,
      stats: "Filtrage & coordination exécutive",
    },
    {
      icon: "🏛️",
      title: "Direction",
      subtitle: "Aria · Sam · Léon · Alex · Pipeline",
      description: `${countAgentsForBureau("hub")} Agents`,
      href: "/hub",
      tier: DEPT_TIERS.hub,
      badge: `${countAgentsForBureau("hub")} Agents`,
      stats: `${countAgentsForBureau("hub")} Agents · ${stats.hubPrCount} PR${stats.hubPrCount !== 1 ? "s" : ""} en attente`,
    },
    {
      icon: "📱",
      title: "Pôle App",
      subtitle: "Naïa App · Eve Journey · Dev mobile & backend",
      description: `${countAgentsForBureau("app")} Agents`,
      href: "/app",
      tier: DEPT_TIERS.app,
      badge: `${countAgentsForBureau("app")} Agents`,
      stats: `${countAgentsForBureau("app")} Agents · ${stats.appOpenTickets} ticket${stats.appOpenTickets !== 1 ? "s" : ""} ouvert${stats.appOpenTickets !== 1 ? "s" : ""}`,
    },
    {
      icon: "🎮",
      title: "Pôle Gaming",
      subtitle: "Wyrdheim Online · Naïa World · UE5 · Lore",
      description: `${countAgentsForBureau("gaming")} Agents`,
      href: "/gaming",
      tier: DEPT_TIERS.gaming,
      badge: `${countAgentsForBureau("gaming")} Agents`,
      stats: stats.gamingStatus,
    },
    {
      icon: "🤖",
      title: "Pôle Robotique",
      subtitle: "Eve Robot · Raspberry Pi · Hardware",
      description: "2 Agents",
      href: "/robo",
      tier: DEPT_TIERS.robo,
      badge: "2 Agents",
      stats: stats.roboStatus,
    },
    {
      icon: "💰",
      title: "Comptabilité",
      subtitle: "Jules · Rémi · Finances · Coûts LLM · Budget",
      description: `${countAgentsForBureau("finances")} Agents`,
      href: "/finances",
      tier: DEPT_TIERS.finances,
      badge: stats.financesMonthTotal,
      stats: `Total ce mois : ${stats.financesMonthTotal}`,
    },
    {
      icon: "📣",
      title: "Marketing",
      subtitle: "Lena · Eliot · Contenu · SEO · Réseaux",
      description: `${countAgentsForBureau("marketing")} Agents`,
      href: "/marketing",
      tier: DEPT_TIERS.marketing,
      badge: `${countAgentsForBureau("marketing")} Agents`,
      stats: `${stats.marketingPendingPosts} post${stats.marketingPendingPosts !== 1 ? "s" : ""} en attente`,
    },
    {
      icon: "🔬",
      title: "R&D",
      subtitle: "Nova · Mira · Brainstorm · Dossiers · Comité",
      description: `${countAgentsForBureau("rd")} Agents`,
      href: "/rd",
      tier: DEPT_TIERS.rd,
      badge: `${countAgentsForBureau("rd")} Agents`,
      stats:
        stats.rdSessions > 0
          ? `${stats.rdSessions} session${stats.rdSessions !== 1 ? "s" : ""} disponibles`
          : "Sessions disponibles",
    },
    {
      icon: "🎨",
      title: "Direction Artistique",
      subtitle: "Brand Kit · Assets · Charte graphique",
      description: "Kits disponibles",
      href: "/brand",
      tier: DEPT_TIERS.brand,
      badge:
        stats.brandKits > 0
          ? `${stats.brandKits} kit${stats.brandKits !== 1 ? "s" : ""}`
          : undefined,
      stats:
        stats.brandKits > 0
          ? `${stats.brandKits} kit${stats.brandKits !== 1 ? "s" : ""} disponible${stats.brandKits !== 1 ? "s" : ""}`
          : "Kits disponibles",
    },
    {
      icon: "📊",
      title: "Reporting",
      subtitle: "Layla · Axel · KPIs · Métriques · Releases",
      description: `${countAgentsForBureau("analytics")} Agents`,
      href: "/analytics",
      tier: DEPT_TIERS.analytics,
      badge: `${countAgentsForBureau("analytics")} Agents`,
      stats: "Données disponibles",
    },
    {
      icon: "🔌",
      title: "IT / Connexions",
      subtitle: "Apps OAuth · Composio · Intégrations",
      description: "Apps connectées",
      href: "/connections",
      tier: DEPT_TIERS.it,
      badge: `${stats.connectedApps} app${stats.connectedApps !== 1 ? "s" : ""}`,
      stats: `${stats.connectedApps} app${stats.connectedApps !== 1 ? "s" : ""} connectée${stats.connectedApps !== 1 ? "s" : ""}`,
    },
    {
      icon: "⚙️",
      title: "Paramètres",
      subtitle: "Modèles LLM · Config agents",
      description: "Choisir le modèle IA par agent",
      href: "/settings",
      tier: DEPT_TIERS.hub,
      badge: "Modèles",
      stats: "Sélection modèle par agent",
    },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-copper/10 bg-obsidian/80 px-6 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <Link href="/" className="opacity-90 transition hover:opacity-100">
            <AlnuaLogo variant="lockup" height={40} />
          </Link>

          <div className="flex items-center gap-6">
            <div className="hidden text-right sm:block">
              <p className="font-title text-sm font-medium text-ivory">
                Bonjour Emilie
              </p>
              <p className="font-body text-xs text-titanium">
                {format(now, "EEEE d MMMM yyyy", { locale: fr })}
              </p>
            </div>
            <Link
              href="/ceo"
              className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-copper/20 bg-obsidian-2 text-titanium transition hover:border-copper/40 hover:text-ivory"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
              {stats.ceoNotifications > 0 ? (
                <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-copper px-1 text-[10px] font-bold text-obsidian">
                  {stats.ceoNotifications}
                </span>
              ) : null}
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-10">
        <div className="mb-10">
          <h1 className="font-title text-4xl font-light tracking-wide text-ivory">
            Siège social <span className="text-copper">ALNUA</span>
          </h1>
          <p className="mt-2 font-body text-sm tracking-wider text-titanium">
            IMAGINATION · TECHNOLOGY · CREATION
          </p>
          <p className="mt-3 font-body text-sm text-titanium/80">
            Choisis un département pour entrer dans ton espace de travail.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {doors.map((door) => (
            <DepartmentDoor key={door.href} {...door} />
          ))}
        </div>

        <section className="mt-12 border-t border-copper/10 pt-8">
          <h2 className="label-caps mb-4">Outils admin</h2>
          <div className="flex flex-wrap gap-3">
            {[
              { href: "/briefing", label: "Briefing" },
              { href: "/beta", label: "Beta testeurs" },
              { href: "/waitlist", label: "Waitlist" },
              { href: "/releases", label: "Releases" },
              { href: "/partnerships/manage", label: "Partenariats" },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-lg border border-copper/20 bg-obsidian-2/60 px-4 py-2 font-body text-sm text-titanium transition hover:border-copper/40 hover:text-ivory"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-copper/10 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between font-body text-xs text-titanium/60">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                !stats.apiOnline
                  ? "bg-red-500"
                  : stats.apiAuthenticated
                    ? "bg-copper-light"
                    : "bg-amber-500"
              )}
            />
            {!stats.apiOnline
              ? "API offline"
              : stats.apiAuthenticated
                ? "API connectée"
                : "Clé API Hub invalide ou absente"}
          </div>
          <span>{format(now, "HH:mm")}</span>
        </div>
      </footer>
    </div>
  );
}
