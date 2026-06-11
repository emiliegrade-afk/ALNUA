"use client";

import { useEffect, useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { Bell } from "lucide-react";
import Link from "next/link";
import { AlnuaLogo } from "@/components/brand/alnua-logo";
import { DepartmentDoor } from "@/components/lobby/department-door";
import { DEPT_TIERS } from "@/lib/dept-colors";
import { fetchLobbyStats, type LobbyStats } from "@/lib/lobby-api";
import { cn } from "@/lib/utils";

const DEFAULT_STATS: LobbyStats = {
  apiOnline: false,
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
  const [loading, setLoading] = useState(true);
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    fetchLobbyStats()
      .then(setStats)
      .catch(() => setStats(DEFAULT_STATS))
      .finally(() => setLoading(false));

    const clock = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(clock);
  }, []);

  const doors = [
    {
      icon: "👑",
      title: "Bureau du CEO",
      subtitle: "Mission Control · Brief · Décisions en attente",
      description: "1 COO Agent",
      href: "/ceo",
      tier: DEPT_TIERS.ceo,
      badge:
        stats.ceoNotifications > 0
          ? `${stats.ceoNotifications} notif${stats.ceoNotifications > 1 ? "s" : ""}`
          : "1 COO Agent",
      stats: `1 COO Agent · ${stats.ceoNotifications} notification${stats.ceoNotifications !== 1 ? "s" : ""}`,
    },
    {
      icon: "🏛️",
      title: "Direction",
      subtitle: "Pipeline codage · PM · QA · Spec",
      description: "4 Agents",
      href: "/hub",
      tier: DEPT_TIERS.hub,
      badge: "4 Agents",
      stats: `4 Agents · ${stats.hubPrCount} PR${stats.hubPrCount !== 1 ? "s" : ""} en attente`,
    },
    {
      icon: "📱",
      title: "Pôle App",
      subtitle: "Naïa App · Eve Journey · Dev · Content",
      description: "2 Agents",
      href: "/app",
      tier: DEPT_TIERS.app,
      badge: "2 Agents",
      stats: `2 Agents · ${stats.appOpenTickets} ticket${stats.appOpenTickets !== 1 ? "s" : ""} ouvert${stats.appOpenTickets !== 1 ? "s" : ""}`,
    },
    {
      icon: "🎮",
      title: "Pôle Gaming",
      subtitle: "Wyrdheim Online · Naïa World · UE5 · Lore",
      description: "3 Agents",
      href: "/gaming",
      tier: DEPT_TIERS.gaming,
      badge: "3 Agents",
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
      subtitle: "Finances · Coûts LLM · Budget · Transactions",
      description: "Total ce mois",
      href: "/finances",
      tier: DEPT_TIERS.finances,
      badge: stats.financesMonthTotal,
      stats: `Total ce mois : ${stats.financesMonthTotal}`,
    },
    {
      icon: "📣",
      title: "Marketing",
      subtitle: "Contenu · SEO · Réseaux · Communauté",
      description: "1 Agent",
      href: "/marketing",
      tier: DEPT_TIERS.marketing,
      badge: "1 Agent",
      stats: `${stats.marketingPendingPosts} post${stats.marketingPendingPosts !== 1 ? "s" : ""} en attente`,
    },
    {
      icon: "🔬",
      title: "R&D",
      subtitle: "Brainstorm · Idées · Sessions · Mémoire",
      description: "1 Agent",
      href: "/rd",
      tier: DEPT_TIERS.rd,
      badge: "1 Agent",
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
      subtitle: "Analytics · KPIs · Métriques · Releases",
      description: "Données disponibles",
      href: "/analytics",
      tier: DEPT_TIERS.analytics,
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

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 11 }).map((_, i) => (
              <div
                key={i}
                className="h-40 animate-pulse rounded-xl bg-obsidian-2"
              />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {doors.map((door) => (
              <DepartmentDoor key={door.href} {...door} />
            ))}
          </div>
        )}
      </main>

      <footer className="border-t border-copper/10 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between font-body text-xs text-titanium/60">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                stats.apiOnline ? "bg-copper-light" : "bg-red-500"
              )}
            />
            API {stats.apiOnline ? "online" : "offline"}
          </div>
          <span>{format(now, "HH:mm")}</span>
        </div>
      </footer>
    </div>
  );
}
